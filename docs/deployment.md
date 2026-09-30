# Deployment Guide

This guide covers all steps required to deploy the GreenLane Maritime platform, from prerequisites through verification.

## Prerequisites

Before deploying, ensure the following tools are installed and configured on your system.

### Docker

GreenLane requires Docker 24.0 or later. Docker provides the container runtime for all backend, frontend, and database services.

```bash
docker --version
# Expected: Docker version 24.0.x or later
```

### Docker Compose

Docker Compose 2.0+ is required. The platform uses `docker compose` (the Compose V2 plugin) for orchestrating all five services.

```bash
docker compose version
# Expected: Docker Compose version v2.x.x
```

### Node.js

The frontend React application requires Node.js 20 or later for building and local development.

```bash
node --version
# Expected: v20.x.x or later
```

### Python

The FastAPI backend requires Python 3.12 or later for local development and testing.

```bash
python --version
# Expected: Python 3.12.x
```

## Environment Setup

### Creating the `.env` File

The platform uses a `.env` file to manage environment variables. Copy the provided example and customize it for your deployment.

```bash
cp .env.example .env
```

Open `.env` and set the following required secrets:

| Variable                    | Description                                      | Example                                  |
|-----------------------------|--------------------------------------------------|------------------------------------------|
| `JWT_SECRET`                | Secret key for signing access tokens             | Generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `REFRESH_SECRET`            | Secret key for signing refresh tokens            | Generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `MONGO_INITDB_ROOT_PASSWORD` | MongoDB admin password                        | Generate with `python -c "import secrets; print(secrets.token_urlsafe(16))"` |
| `CORS_ORIGINS`              | Allowed frontend origins                         | `http://localhost:3000,http://localhost:5173` |

**Important:** The `JWT_SECRET` and `REFRESH_SECRET` must be cryptographically strong random strings. The application will refuse to start if either is set to the default placeholder value.

### Environment Variables Reference

All environment variables are loaded from `.env` and consumed by the backend application via `pydantic-settings`. The configuration is defined in `backend/app/core/config.py`.

| Variable                  | Default                          | Description                                    |
|---------------------------|----------------------------------|------------------------------------------------|
| `MONGODB_URL`             | `mongodb://localhost:27017`      | MongoDB connection string                      |
| `DATABASE_NAME`           | `greenlane_db`                   | Database name                                  |
| `REDIS_URL`               | `redis://localhost:6379`         | Redis connection URL                           |
| `JWT_SECRET`              | (required, no default)           | JWT signing secret                             |
| `REFRESH_SECRET`          | (required, no default)           | Refresh token signing secret                   |
| `ALGORITHM`               | `HS256`                          | JWT algorithm                                  |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15`                          | Access token expiry in minutes                 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7`                           | Refresh token expiry in days                   |
| `CORS_ORIGINS`            | `http://localhost:3000,...`      | Comma-separated allowed CORS origins            |
| `LOG_LEVEL`               | `INFO`                           | Application logging level                      |
| `ENVIRONMENT`             | `development`                    | `development` or `production`                  |

## SSL/TLS Setup

GreenLane uses nginx as a reverse proxy with TLS termination. Self-signed certificates are generated for development; Let's Encrypt certificates can be configured for production.

### Generating Certificates

Run the certificate generation script to create self-signed TLS certificates:

```bash
./generate_certs.sh generate
```

This creates the following files in the `certs/` directory:

- `certs/server.crt` — Server TLS certificate
- `certs/server.key` — Server TLS private key
- `certs/ca.crt` — Certificate authority certificate

**For production deployments**, integrate with Let's Encrypt by setting `TLS_REDIRECT=true` and configuring the `generate_certs.sh` script to use `certbot`. See the audit report for details on the certbot integration.

### Checking Certificate Expiry

```bash
./generate_certs.sh check
```

### Auto-Renewal

```bash
./generate_certs.sh auto-renew
```

## Quick Start

The fastest way to get the platform running is:

```bash
# Build all Docker images
make build

# Start all services in detached mode
make up

# Verify the deployment
make verify
```

Or equivalently:

```bash
docker compose up -d --build
```

This starts all five services: backend, frontend, mongo, redis, and nginx. The `celery` worker starts automatically as a separate service for background task processing.

**Note:** The `make up` command uses `docker compose up -d`, which runs all containers in the background. Use `make down` to stop everything.

## Database Initialization

The backend automatically initializes the database and creates all required indexes on startup via the `lifespan` function in `backend/app/main.py`. This calls `init_db_indexes()` which creates the following indexes:

- **users**: unique email, org_id index
- **ships**: unique (org_id, imo_number), status, compliance_status, name indexes
- **voyages**: (org_id, asset_id), (org_id, departure_date), created_at indexes
- **emissions_computed**: (voyage_id, is_current), (org_id, calculated_at), unique partial index on (voyage_id, is_current)
- **reports**: (org_id, year), (org_id, generated_at) indexes
- **audit_logs**: (org_id, timestamp) with 1-year TTL, timestamp index

To manually trigger index initialization or check index status, connect to the backend container:

```bash
make shell-backend
```

Then run the initialization code directly if needed.

## Verification

After deployment, verify that all services are running correctly.

### PowerShell Verification (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File verify.ps1
```

This script checks:
1. All critical files exist
2. Security configuration is correct (Redis blacklist, token validation)
3. Database connection and authentication
4. Docker services are healthy
5. Environment variables are properly set

### Manual Verification

Check service health:

```bash
# Check all services are running
docker compose ps

# Check service logs for errors
make logs

# Verify backend health
curl -k https://localhost/health

# Verify frontend is serving
curl http://localhost:3000
```

Expected health response: `{"status": "healthy"}`

## Health Checks

The platform implements health checks at multiple levels:

| Component   | Check                                  | Interval  | Timeout |
|-------------|----------------------------------------|-----------|---------|
| Backend     | `/health` endpoint (DB ping)           | Built-in  | —       |
| Frontend    | `nginx` health check                   | 30s       | 5s      |
| MongoDB     | `mongosh` ping                         | 10s       | 5s      |
| Redis       | `PING` command                         | Docker    | —       |

The backend `/health` endpoint returns `{"status": "healthy"}` when MongoDB is reachable, or `{"status": "degraded"}` with HTTP 503 when the database is unreachable. No internal infrastructure details are exposed in the health response.

## Troubleshooting

### Common Issues

**1. Services fail to start**

```bash
# Check if Docker is running
docker info

# View all container logs
docker compose logs

# Restart the stack
make down && make up
```

**2. MongoDB connection errors**

Ensure the `MONGO_INITDB_ROOT_PASSWORD` in `.env` matches what docker-compose.yml expects. Check that the MongoDB container is healthy:

```bash
docker compose ps mongo
docker compose logs mongo
```

**3. JWT_SECRET or REFRESH_SECRET not set**

The application validates that these are not default placeholder values on startup. Generate new secrets:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**4. CORS errors**

Ensure `CORS_ORIGINS` in `.env` includes the frontend origin. The backend restricts CORS to explicit methods (`GET, POST, PUT, PATCH, DELETE, OPTIONS`) and headers (`Authorization, Content-Type`).

**5. Certificate errors in development**

Self-signed certificates trigger browser warnings. To bypass in Chrome, visit `chrome://flags/#allow-insecure-localhost` or accept the risk manually. For production, use Let's Encrypt certificates.

**6. Port already in use**

If ports 80, 443, 8000, or 5173 are already occupied:

```bash
# Find what's using the port
lsof -i :80
lsof -i :443

# Stop conflicting services or change port mappings in docker-compose.yml
```

**7. Frontend build fails**

```bash
# Rebuild frontend dependencies
cd frontend && npm ci && npm run build

# Or rebuild from scratch
make clean && make build && make up
```

**8. Redis connection failures**

The token blacklist depends on Redis. If Redis is unavailable, the backend may fail authentication checks. Verify Redis is running:

```bash
docker compose ps redis
docker compose logs redis
```
