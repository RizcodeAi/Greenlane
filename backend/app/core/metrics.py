"""Prometheus metrics infrastructure for GreenLane Maritime backend."""

import time

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
)
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

# --- Histogram buckets ---
BUCKETS = (.01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10)

# --- HTTP request metrics ---
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=BUCKETS,
)

# --- MongoDB metrics ---
mongodb_query_duration_seconds = Histogram(
    "mongodb_query_duration_seconds",
    "MongoDB query duration in seconds",
    buckets=BUCKETS,
)

active_connections = Gauge(
    "active_connections",
    "Number of active database connections",
)

# --- Business metrics ---
report_generation_requests_total = Counter(
    "report_generation_requests_total",
    "Total report generation requests",
)

emissions_records_total = Counter(
    "emissions_records_total",
    "Total emissions records processed",
)


def metrics_init():
    """Register all Prometheus metrics at application startup.

    Metrics are defined as module-level singletons, which are automatically
    registered with the default Prometheus registry on construction.
    This function serves as the explicit initialization hook called from
    the FastAPI lifespan so that metrics exist before any requests arrive.
    """
    return


class MetricsMiddleware(BaseHTTPMiddleware):
    """Async Starlette middleware that records HTTP request metrics."""

    async def dispatch(self, request: Request, call_next):
        method = request.method
        endpoint = request.url.path
        start_time = time.monotonic()

        response: Response = await call_next(request)
        status_code = response.status_code

        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
        ).inc()

        duration = time.monotonic() - start_time
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint,
        ).observe(duration)

        return response


def record_db_duration(start_time: float):
    """Record a MongoDB query duration observation.

    Pass the value returned by time.monotonic() captured before the query,
    and this function computes the delta and records it.
    """
    elapsed = time.monotonic() - start_time
    mongodb_query_duration_seconds.observe(elapsed)


async def metrics_endpoint(request: Request) -> Response:
    """Return the Prometheus metrics payload. No authentication required."""
    return Response(
        content=generate_latest(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
