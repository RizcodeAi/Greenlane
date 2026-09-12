from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import redis.asyncio as aioredis
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_redis_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None or _redis_pool.connection_pool.disconnected:
        _redis_pool = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    return _redis_pool


async def blacklist_token(token: str) -> None:
    """Add a token to the Redis blacklist with TTL."""
    redis = await get_redis()
    # Decode the token to get the expiry and set TTL accordingly
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        exp = payload.get("exp")
        if exp:
            ttl = max(exp - int(datetime.now(timezone.utc).timestamp()), 0)
            await redis.setex(f"bl:{token}", ttl, "1")
    except JWTError:
        await redis.setex(f"bl:{token}", 86400, "1")


async def verify_access_token(token: str) -> Optional[dict]:
    try:
        redis = await get_redis()
        if await redis.exists(f"bl:{token}"):
            return None
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


async def verify_refresh_token(token: str) -> Optional[dict]:
    try:
        redis = await get_redis()
        if await redis.exists(f"bl:{token}"):
            return None
        payload = jwt.decode(token, settings.REFRESH_SECRET, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
