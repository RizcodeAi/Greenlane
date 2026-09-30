# GreenLane Maritime Platform — Documentation

GreenLane is a fleet emissions tracking and management platform built for maritime compliance with IMO DCS standards. This documentation covers all aspects of deploying, operating, and integrating with the platform.

## Table of Contents

- [Deployment Guide](deployment.md) — Step-by-step instructions for deploying the platform
- [Architecture Overview](architecture.md) — System design, data flows, and service responsibilities
- [API Reference](api.md) — Complete API endpoint documentation with schemas
- [Monitoring & Observability](monitoring.md) — Health checks, metrics, and alerting

## Quick Start

```bash
# Clone the repository
git clone <repo-url> greenlane
cd greenlane

# Copy environment file and set secrets
cp .env.example .env
# Edit .env to add JWT_SECRET and REFRESH_SECRET

# Start all services
make up

# Verify the deployment
make verify
```

## System Requirements

- Docker 24.0+
- Docker Compose 2.0+
- Node.js 20+ (for frontend development)
- Python 3.12+ (for backend development)
- OpenSSL (for certificate generation)

## Services

| Service   | Port  | Description                              |
|-----------|-------|------------------------------------------|
| nginx     | 80/443| Reverse proxy with SSL termination       |
| backend   | 8000  | FastAPI application                      |
| frontend  | 5173  | React app served via nginx               |
| mongo     | 27017 | MongoDB database (internal only)         |
| redis     | 6379  | Redis for token blacklist and caching     |
| celery    | —     | Background task worker for report generation |

## Support

For issues, questions, or contributions, refer to the `AUDIT_REPORT.md` for security audit details and the `SECURITY.md` for security practices.
