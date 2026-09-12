import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from bson import ObjectId

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token, create_refresh_token,
    verify_access_token, verify_refresh_token,
    hash_password, verify_password, blacklist_token, pwd_context,
)
from app.services.audit_log import log_audit
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.api.v1.deps import get_current_tenant_user, require_role, security

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    org_name: str
    industry: str
    invite_emails: Optional[List[str]] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class InviteRequest(BaseModel):
    emails: List[str]
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/minute")
async def register(req: RegisterRequest, db: AsyncIOMotorDatabase = Depends(get_db), response: Response = None):
    existing = await db["users"].find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    org_id = str(ObjectId())
    org = {
        "_id": org_id,
        "name": req.org_name,
        "industry": req.industry,
        "created_at": datetime.now(timezone.utc),
    }
    await db["organizations"].insert_one(org)

    hashed = pwd.hash(req.password)
    user = {
        "_id": str(ObjectId()),
        "email": req.email,
        "full_name": req.full_name,
        "hashed_password": hashed,
        "role": "Org Admin",
        "org_id": org_id,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }
    await db["users"].insert_one(user)

    if req.invite_emails:
        for email in req.invite_emails:
            invite_temp = secrets.token_urlsafe(16)
            invite_user = {
                "_id": str(ObjectId()),
                "email": email,
                "full_name": email.split("@")[0].title(),
                # TODO: Email temp_password to the user and force a password reset on first login
                "hashed_password": pwd.hash(invite_temp),
                "role": "Operator",
                "org_id": org_id,
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
            }
            await db["users"].insert_one(invite_user)
        await log_audit(db, org_id, user["_id"], "invite", "organization", org_id, {"invited": req.invite_emails, "role": req.role})

    access_token = create_access_token(data={"sub": user["_id"], "org_id": org_id, "role": "Org Admin"})
    refresh_token = create_refresh_token(data={"sub": user["_id"], "org_id": org_id})

    response.set_cookie(
        key="refresh_token", value=refresh_token,
        httponly=True, secure=settings.environment != "development", samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth/refresh",
    )
    await log_audit(db, org_id, user["_id"], "register", "organization", org_id)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(req: LoginRequest, db: AsyncIOMotorDatabase = Depends(get_db), response: Response = None):
    user = await db["users"].find_one({"email": req.email, "is_active": True})
    if not user or not pwd.verify(req.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user["_id"], "org_id": user["org_id"], "role": user["role"]})
    refresh_token = create_refresh_token(data={"sub": user["_id"], "org_id": user["org_id"]})

    response.set_cookie(
        key="refresh_token", value=refresh_token,
        httponly=True, secure=settings.environment != "development", samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth/refresh",
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(request: Request, response: Response = None, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(get_current_tenant_user)):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await blacklist_token(refresh_token)
    response.delete_cookie(key="refresh_token", path="/api/v1/auth/refresh")
    # Blacklist the access token
    credentials = request.headers.get("Authorization", "")
    if credentials.startswith("Bearer "):
        await blacklist_token(credentials[7:])
    await log_audit(db, current_user["org_id"], current_user["user"]["_id"], "logout", "session", current_user["user"]["_id"])
    return {"message": "Logged out"}


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("5/minute")
async def refresh(request: Request, db: AsyncIOMotorDatabase = Depends(get_db), response: Response = None):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    payload = await verify_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # Blacklist the old refresh token before issuing a new one
    await blacklist_token(refresh_token)

    user = await db["users"].find_one({"_id": payload.get("sub"), "org_id": payload.get("org_id")})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    access_token = create_access_token(data={"sub": user["_id"], "org_id": user["org_id"], "role": user["role"]})
    new_refresh_token = create_refresh_token(data={"sub": user["_id"], "org_id": user["org_id"]})

    response.set_cookie(
        key="refresh_token", value=new_refresh_token,
        httponly=True, secure=settings.environment != "development", samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth/refresh",
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_tenant_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    user = current_user["user"]
    org = await db["organizations"].find_one({"_id": user["org_id"]})
    return {
        "user": {
            "id": str(user["_id"]), "email": user["email"],
            "full_name": user["full_name"], "role": user["role"],
            "org_id": user["org_id"], "is_active": user["is_active"],
            "created_at": user["created_at"],
        },
        "organization": org,
    }


@router.post("/invite")
@limiter.limit("3/minute")
async def invite(req: InviteRequest, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_role("Org Admin"))):
    if req.role not in ["Operator"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot invite users with that role")
    org_id = current_user["org_id"]
    invited = []
    for email in req.emails:
        existing = await db["users"].find_one({"email": email, "org_id": org_id})
        if existing:
            invited.append({"email": email, "status": "already_exists"})
            continue
        # TODO: Email temp_password to the user and force a password reset on first login
        temp_password = secrets.token_urlsafe(16)
        new_user = {
            "_id": str(ObjectId()),
            "email": email,
            "full_name": email.split("@")[0].title(),
            "hashed_password": pwd.hash(temp_password),
            "role": "Operator",
            "org_id": org_id,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
        await db["users"].insert_one(new_user)
        invited.append({"email": email, "status": "invited", "role": "Operator"})

    await log_audit(db, org_id, current_user["user"]["_id"], "invite", "organization", org_id, {"invited": req.emails, "role": req.role})
    return {"invited": invited}
