import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from bson import ObjectId
from bson.errors import InvalidId

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token, create_refresh_token,
    verify_access_token, verify_refresh_token,
    hash_password, verify_password, blacklist_token, pwd_context,
    set_access_token_cookie, clear_access_token_cookie,
)
from app.core.csrf import generate_csrf_token, store_csrf_token, validate_csrf_token, csrf_protect
from app.services.audit_log import log_audit
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.api.v1.deps import get_current_tenant_user, require_role, security

router = APIRouter()

def validate_object_id(id_str: str):
    try:
        return ObjectId(id_str)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format")

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
async def register(request: Request, req: RegisterRequest, db: AsyncIOMotorDatabase = Depends(get_db), response: Response = None):
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
    hashed = pwd_context.hash(req.password)
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

    try:
        await db["organizations"].insert_one(org)
        await db["users"].insert_one(user)
    except Exception as e:
        await db["organizations"].delete_one({"_id": org_id})
        raise HTTPException(status_code=500, detail="Registration failed, rolled back.")

    if req.invite_emails:
        for email in req.invite_emails:
            invite_temp = secrets.token_urlsafe(16)
            invite_user = {
                "_id": str(ObjectId()),
                "email": email,
                "full_name": email.split("@")[0].title(),
                "hashed_password": pwd_context.hash(invite_temp),
                "role": "Operator",
                "org_id": org_id,
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
            }
            await db["users"].insert_one(invite_user)
        await log_audit(db, org_id, user["_id"], "invite", "organization", org_id, {"invited": req.invite_emails, "role": req.role})

    access_token = create_access_token(data={"sub": user["_id"], "org_id": org_id, "role": "Org Admin"})
    refresh_token = create_refresh_token(data={"sub": user["_id"], "org_id": org_id})

    set_access_token_cookie(response, access_token, max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    response.set_cookie(
        key="refresh_token", value=refresh_token,
        httponly=True, secure=settings.environment != "development", samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth/refresh",
    )

    # Generate and store CSRF token
    csrf_token = generate_csrf_token()
    session_id = refresh_token
    await store_csrf_token(session_id, csrf_token)
    response.set_cookie(
        key="csrf_token", value=csrf_token,
        httponly=False, secure=settings.environment != "development", samesite="lax",
        path="/",
    )
    response.headers["access-control-expose-headers"] = "X-CSRF-Token"
    response.headers["X-CSRF-Token"] = csrf_token

    await log_audit(db, org_id, user["_id"], "register", "organization", org_id)
    return {"access_token": access_token, "token_type": "bearer", "csrf_token": csrf_token}


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, req: LoginRequest, db: AsyncIOMotorDatabase = Depends(get_db), response: Response = None):
    user = await db["users"].find_one({"email": req.email, "is_active": True})
    if not user or not pwd_context.verify(req.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user["_id"], "org_id": user["org_id"], "role": user["role"]})
    refresh_token = create_refresh_token(data={"sub": user["_id"], "org_id": user["org_id"]})

    set_access_token_cookie(response, access_token, max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    response.set_cookie(
        key="refresh_token", value=refresh_token,
        httponly=True, secure=settings.environment != "development", samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth/refresh",
    )

    # Generate and store CSRF token
    csrf_token = generate_csrf_token()
    session_id = refresh_token
    await store_csrf_token(session_id, csrf_token)
    response.set_cookie(
        key="csrf_token", value=csrf_token,
        httponly=False, secure=settings.environment != "development", samesite="lax",
        path="/",
    )
    response.headers["access-control-expose-headers"] = "X-CSRF-Token"
    response.headers["X-CSRF-Token"] = csrf_token

    return {"access_token": access_token, "token_type": "bearer", "csrf_token": csrf_token}


@router.post("/logout")
async def logout(request: Request, response: Response = None, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(get_current_tenant_user), _= Depends(csrf_protect)):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await blacklist_token(refresh_token)
    response.delete_cookie(key="refresh_token", path="/api/v1/auth/refresh")
    clear_access_token_cookie(response)
    # Blacklist the access token from cookie
    access_token = request.cookies.get("access_token")
    if access_token:
        await blacklist_token(access_token)
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

    await blacklist_token(refresh_token)

    user = await db["users"].find_one({"_id": payload.get("sub"), "org_id": payload.get("org_id")})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    access_token = create_access_token(data={"sub": user["_id"], "org_id": user["org_id"], "role": user["role"]})
    new_refresh_token = create_refresh_token(data={"sub": user["_id"], "org_id": user["org_id"]})

    set_access_token_cookie(response, access_token, max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
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
async def invite(request: Request, req: InviteRequest, db: AsyncIOMotorDatabase = Depends(get_db), current_user: dict = Depends(require_role("Org Admin")), _= Depends(csrf_protect)):
    if req.role not in ["Operator"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot invite users with that role")
    org_id = current_user["org_id"]
    invited = []
    for email in req.emails:
        existing = await db["users"].find_one({"email": email, "org_id": org_id})
        if existing:
            invited.append({"email": email, "status": "already_exists"})
            continue
        temp_password = secrets.token_urlsafe(16)
        new_user = {
            "_id": str(ObjectId()),
            "email": email,
            "full_name": email.split("@")[0].title(),
            "hashed_password": pwd_context.hash(temp_password),
            "role": "Operator",
            "org_id": org_id,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
        await db["users"].insert_one(new_user)
        invited.append({"email": email, "status": "invited", "role": "Operator"})

    await log_audit(db, org_id, current_user["user"]["_id"], "invite", "organization", org_id, {"invited": req.emails, "role": req.role})
    return {"invited": invited}
