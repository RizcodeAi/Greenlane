from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

from app.core.config import settings
from app.core.database import client, close_db, init_db_indexes, db
from app.core.logging import setup_logging
from app.api.v1 import auth
from app.api.v1 import fleet
from app.api.v1 import dashboard
from app.api.v1 import emissions
from app.api.v1 import reports


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'"
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.limiter = auth.limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    setup_logging()
    await init_db_indexes(db)
    yield
    await close_db()


app = FastAPI(
    title="GreenLane API",
    description="Fleet emissions tracking and management platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(fleet.router, prefix="/api/v1/fleet", tags=["Fleet Management"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(emissions.router, prefix="/api/v1/emissions", tags=["Emissions"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


@app.get("/health", tags=["Health"])
async def health_check():
    try:
        await db.command("ping")
        return {"status": "healthy"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded"},
        )
