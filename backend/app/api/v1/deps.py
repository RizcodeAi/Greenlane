from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status, Request

from app.core.database import get_db
from app.core.security import verify_access_token

security = HTTPBearer(auto_error=False)


async def get_current_tenant_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    # Try to get token from cookie first (HttpOnly cookie-based auth)
    token = request.cookies.get("access_token")

    # Fall back to Authorization header for backward compatibility
    if not token and credentials:
        token = credentials.credentials

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = await verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user_id = payload.get("sub")
    org_id = payload.get("org_id")
    role = payload.get("role", "Operator")
    user = await db["users"].find_one({"_id": user_id, "org_id": org_id, "is_active": True})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # Verify role hasn't changed in the database
    if user["role"] != role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return {"user": user, "org_id": org_id, "role": role}


def require_role(*allowed: str):
    async def role_check(current_user: dict = Depends(get_current_tenant_user)):
        if current_user["role"] not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return role_check
