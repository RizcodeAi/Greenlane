"""JSON-formatted logging configuration with Request ID / correlation tracing for GreenLane Maritime."""

import contextvars
import logging
import json
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# --- ContextVar for request-scoped tracing ---

trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "trace_id", default=""
)
span_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "span_id", default=""
)
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)


def trace_request(request_id: str) -> str:
    """Create a trace context for the given request_id.

    Sets the request_id, trace_id, and a new span_id in contextvars
    so that all downstream log records carry the same correlation data.

    Returns the request_id that was set.
    """
    trace_id_var.set(request_id)
    request_id_var.set(request_id)
    span_id_var.set(uuid.uuid4().hex[:8])
    return request_id


def clear_trace() -> None:
    """Reset all trace-related contextvars to defaults."""
    trace_id_var.set("")
    request_id_var.set("")
    span_id_var.set("")


# --- Filter ---

class RequestIDFilter(logging.Filter):
    """Add request_id, trace_id, and span_id to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("")
        record.trace_id = trace_id_var.get("")
        record.span_id = span_id_var.get("")
        return True


# --- Helper functions ---

def log_request_start(
    method: str,
    path: str,
    request_id: str,
    headers: dict[str, str] | None = None,
) -> None:
    """Log the start of a request at INFO level."""
    logger = logging.getLogger("greenlane.request")
    extra: dict[str, Any] = {
        "request_id": request_id,
        "trace_id": trace_id_var.get(""),
        "span_id": span_id_var.get(""),
        "method": method,
        "path": path,
    }
    if headers:
        extra["headers"] = headers
    logger.info("Request started", extra=extra)


def log_request_end(
    method: str,
    path: str,
    request_id: str,
    status_code: int,
    duration_ms: float,
) -> None:
    """Log the end of a request at INFO level."""
    logger = logging.getLogger("greenlane.request")
    logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "trace_id": trace_id_var.get(""),
            "span_id": span_id_var.get(""),
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
        },
    )


# --- Enhanced JSON Formatter ---

class JSONFormatter(logging.Formatter):
    """Emit log records as JSON lines with full request tracing context.

    Output format:
        {"timestamp":..., "level":..., "request_id":..., "method":...,
         "path":..., "duration_ms":..., "trace_id":..., "span_id":...,
         "message":...}
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "request_id": getattr(record, "request_id", ""),
            "trace_id": getattr(record, "trace_id", ""),
            "span_id": getattr(record, "span_id", ""),
            "method": getattr(record, "method", ""),
            "path": getattr(record, "path", ""),
            "duration_ms": getattr(record, "duration_ms", None),
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


# --- Middleware ---

class LoggerMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that generates a unique request_id per request,
    sets it in contextvars, logs request start/end, and adds correlation
    headers to the response.

    Must be added BEFORE SecurityHeadersMiddleware so that the response
    headers X-Request-ID and X-Trace-ID are present when security headers
    are applied.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = uuid.uuid4().hex
        trace_request(request_id)

        method = request.method
        path = request.url.path
        headers = dict(request.headers)

        log_request_start(method, path, request_id, headers)

        start_time = datetime.now(timezone.utc)

        response: Response = await call_next(request)

        end_time = datetime.now(timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = request_id

        log_request_end(method, path, request_id, response.status_code, duration_ms)

        clear_trace()

        return response


# --- Setup ---

def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger with JSON formatting and RequestIDFilter."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    handler.addFilter(RequestIDFilter())
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    # Ensure the greenlane.request logger also uses the handler
    request_logger = logging.getLogger("greenlane.request")
    request_logger.addHandler(handler)
    request_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    request_logger.propagate = True
