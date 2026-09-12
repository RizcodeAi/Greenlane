# Monitoring & Observability

This document describes the monitoring infrastructure, health check endpoints, metrics, and alerting configuration for the GreenLane Maritime platform.

## Health Check Endpoints

### GET /health

The backend application exposes a health check endpoint for load balancers, Docker health checks, and manual verification.

**Request:**
```bash
curl -k https://localhost/health
```

**Successful Response (200):**
```json
{"status": "healthy"}
```

**Degraded Response (503):**
```json
{"status": "degraded"}
```

The endpoint attempts to ping MongoDB. If the database is unreachable, it returns a degraded status with HTTP 503. No internal infrastructure details (such as database connectivity status) are exposed in the response to prevent information disclosure.

### Nginx Health Check

The nginx service includes a health check endpoint proxied to the backend:

```bash
curl http://localhost/health
```

This is configured without rate limiting in the nginx configuration for reliable health monitoring.

## Prometheus Metrics

### GET /metrics

The backend exposes Prometheus-compatible metrics for monitoring and alerting. This endpoint is powered by `prometheus-client`.

**Request:**
```bash
curl -k https://localhost/metrics
```

**Response Format:** Prometheus text exposition format

The metrics middleware (`metrics.py`) instruments the application with request counters, response time histograms, and error counters. Metrics include:

- `http_requests_total` — Total HTTP requests by method, endpoint, and status code
- `http_request_duration_seconds` — Request duration histogram
- `http_requests_in_flight` — Currently in-flight requests
- Application-specific metrics for voyage processing, emissions calculations, and report generation

### Metrics Middleware

The `metrics_init()`, `metrics_middleware()`, and `metrics_endpoint()` functions in `backend/app/core/metrics.py` provide the instrumentation layer. Metrics are collected on every request and exposed via the `/metrics` endpoint.

## Docker Service Health Checks

Each service in `docker-compose.yml` has health check configurations:

| Service   | Health Check Command                        | Interval | Timeout | Retries |
|-----------|---------------------------------------------|----------|---------|---------|
| backend   | `python -c "from app.main import app; import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"` | 30s | 5s | 3 |
| frontend  | `wget -qO- http://localhost/health`         | 30s      | 5s      | 3 |
| mongo     | `echo 'db.runCommand("ping").ok' \| mongosh --quiet` | 10s | 5s | 5 |
| redis     | Docker default (PING command)               | —        | —       | — |

### Checking Service Health

```bash
# Check all service health statuses
docker compose ps

# Check specific service health
docker inspect --format='{{.State.Status}} {{.State.Health.Status}}' greenlane-backend-1

# View health check logs
docker compose logs backend
docker compose logs mongo
```

## Log Format

### Backend Logs (JSON)

The backend application uses structured JSON logging. Log entries follow this format:

```json
{
  "timestamp": "2026-06-15T10:30:00Z",
  "level": "INFO",
  "logger": "app.api.v1.emissions",
  "message": "Voyage created",
  "org_id": "org_xyz",
  "voyage_id": "voyage_001"
}
```

Logging is configured via `backend/app/core/logging.py` with the `setup_logging()` function. The log level is controlled by the `LOG_LEVEL` environment variable (default: `INFO`).

### Nginx Logs (JSON)

Nginx access logs use a custom JSON format defined in `nginx.conf`:

```json
{
  "time_local": "15/Jun/2026:10:30:00 +0000",
  "remote_addr": "192.168.1.1",
  "request": "GET /api/v1/emissions/voyages HTTP/1.1",
  "status": 200,
  "body_bytes_sent": 1234,
  "http_referer": "https://greenlane.local/",
  "http_user_agent": "Mozilla/5.0...",
  "request_time": 0.045
}
```

### Frontend Logs

Frontend logs are output to the browser console. In production, the React application runs via nginx, so client-side errors should be captured by frontend error boundaries and sent to a log aggregation service.

## Monitoring with Prometheus and Grafana

### Architecture

```
┌──────────┐    scrape    ┌──────────────┐    query    ┌──────────────┐
│ Prometheus │───────────▶│  GreenLane   │───────────▶│   Grafana    │
│            │            │  Backend     │            │   Dashboards │
└──────────┘   /metrics   └──────────────┘            └──────────────┘
                           │
                           │ scrape
                           ▼
                      ┌──────────┐
                      │   nginx  │
                      └──────────┘
```

### Prometheus Configuration

Prometheus should be configured to scrape the following targets:

```yaml
scrape_configs:
  - job_name: 'greenlane-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'greenlane-nginx'
    static_configs:
      - targets: ['nginx:80']
```

### Grafana Dashboards

Future Grafana dashboards should include:

- **Service Health Dashboard** — Uptime, response times, error rates per service
- **API Metrics Dashboard** — Request rates, latency percentiles, status code distributions
- **Database Dashboard** — MongoDB connection pool usage, query latency, index hit rates
- **Emissions Processing Dashboard** — Voyages processed per hour, emissions calculation throughput
- **Report Generation Dashboard** — Celery task queue depth, task completion rates, PDF generation times

## Alert Rules

### Critical Alerts

| Alert Name              | Condition                                      | Severity | Action                |
|-------------------------|------------------------------------------------|----------|-----------------------|
| `BackendDown`           | Backend health check fails for >30s            | Critical | Check container logs  |
| `MongoDBDown`           | MongoDB health check fails for >30s            | Critical | Check MongoDB container |
| `RedisDown`             | Redis health check fails for >30s              | Critical | Check Redis container  |
| `HighErrorRate`         | HTTP 5xx error rate >5% over 5 minutes         | Critical | Investigate application |
| `TokenBlacklistFailed`  | Redis connection failures detected             | Critical | Check Redis availability |

### Warning Alerts

| Alert Name                  | Condition                                        | Severity | Action               |
|-----------------------------|--------------------------------------------------|----------|----------------------|
| `HighLatency`               | P95 response time >2s for 5 minutes              | Warning  | Check backend performance |
| `RateLimitExceeded`         | Rate limit exceeded for any endpoint             | Warning  | Review client behavior |
| `LowDiskSpace`              | Docker volume usage >80%                         | Warning  | Clean up volumes     |
| `CertificateExpiring`       | TLS certificate expires in <30 days              | Warning  | Renew certificates   |
| `ReportQueueBacklog`        | Celery queue has >10 pending tasks for >5 min    | Warning  | Scale Celery workers |
| `HealthDegraded`            | Health endpoint returns degraded status           | Warning  | Check database connectivity |

### Alertmanager Configuration

For production deployments, configure Alertmanager to route alerts to:
- Email notifications for Critical alerts
- Slack/Teams channels for Warning alerts
- PagerDuty integration for on-call rotation (Critical only)

## Future Monitoring Enhancements

The following monitoring capabilities are planned:

1. **Structured Logging Pipeline** — Ship JSON logs to Elasticsearch or Loki for centralized search and analysis
2. **Request ID / Correlation ID** — Add unique request IDs to trace requests across services
3. **Distributed Tracing** — Implement OpenTelemetry for end-to-end request tracing
4. **Custom Metrics** — Add business metrics (voyages per org, emissions per vessel) to Prometheus
5. **GPU Metrics** — If using GPU-accelerated report generation, add GPU utilization metrics
6. **Docker Stats Exporter** — Export container CPU, memory, and network metrics to Prometheus
7. **Certificate Monitoring** — Automated certificate expiry checks with alerts
8. **Audit Log Monitoring** — Real-time alerts for suspicious audit log patterns
