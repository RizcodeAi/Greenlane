"""CSRF protection using the double-submit cookie pattern.

Tokens are generated with secrets.token_hex(32), stored in Redis per session,
and validated via hmac.compare_digest against the X-CSRF-Token header.
"""

import secrets
import hmac
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException, status

from app.core.config import settings
from app.core.security import get_redis


STATE_CHANGING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def generate_csrf_token() -> str:
    """Generate a cryptographically random CSRF token."""
    return secrets.token_hex(32)


async def store_csrf_token(session_id: str, token: str) -> None:
    """Store a CSRF token in Redis keyed by session_id with a 1-hour TTL."""
    redis = await get_redis()
    await redis.setex(f"csrf:{session_id}", 3600, token)


async def get_csrf_token(session_id: str) -> Optional[str]:
    """Retrieve a CSRF token from Redis by session_id."""
    redis = await get_redis()
    return await redis.get(f"csrf:{session_id}")


async def validate_csrf_token(request: Request) -> None:
    """Validate the CSRF token from the X-CSRF-Token header against the csrf_token cookie.

    Raises HTTPException(403) if validation fails or tokens are missing.
    Uses hmac.compare_digest to prevent timing attacks.
    """
    header_token = request.headers.get("X-CSRF-Token")
    cookie_token = request.cookies.get("csrf_token")

    if not header_token or not cookie_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing",
        )

    if not hmac.compare_digest(header_token, cookie_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token validation failed",
        )


async def get_session_id(request: Request) -> Optional[str]:
    """Extract the session identifier from the refresh_token cookie or Authorization header."""
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        return refresh_token

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]

    return None


async def csrf_protect(request: Request) -> None:
    """Dependency that validates CSRF tokens on state-changing requests.

    GET and HEAD requests are skipped (read-only).
    For state-changing methods, validates the CSRF token via validate_csrf_token.
    """
    if request.method in STATE_CHANGING_METHODS:
        await validate_csrf_token(request)


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware that handles CSRF token generation and validation.

    For state-changing methods, reads X-CSRF-Token header and validates
    against the csrf_token cookie. Sets the csrf_token cookie on first
    request for new sessions. Adds access-control-expose-headers for CORS.
    """

    async def dispatch(self, request: Request, call_next):
        # Generate CSRF token for sessions that don't have one yet
        session_id = await get_session_id(request)
        if session_id:
            existing_token = await get_csrf_token(session_id)
            if existing_token is None:
                new_token = generate_csrf_token()
                await store_csrf_token(session_id, new_token)
                request.state._csrf_token = new_token
                request.state._csrf_session_id = session_id

        # Validate CSRF for state-changing methods
        if request.method in STATE_CHANGING_METHODS:
            await validate_csrf_token(request)

        response = await call_next(request)

        # Set csrf_token cookie if we generated a new one
        if hasattr(request.state, "_csrf_token") and request.state._csrf_token:
            response.set_cookie(
                key="csrf_token",
                value=request.state._csrf_token,
                httponly=False,  # Frontend needs to read this
                secure=settings.environment != "development",
                samesite="lax",
                path="/",
            )
            # Expose X-CSRF-Token in CORS headers so frontend can read it
            response.headers["access-control-expose-headers"] = "X-CSRF-Token"
            # Also set it as a response header
            response.headers["X-CSRF-Token"] = request.state._csrf_token

        elif request.method in STATE_CHANGING_METHODS:
            # For state-changing requests, ensure the CORS header is set
            response.headers["access-control-expose-headers"] = "X-CSRF-Token"

        return response
