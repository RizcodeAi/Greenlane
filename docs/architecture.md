# Architecture Overview

This document describes the system architecture of the GreenLane Maritime platform, including its technology stack, service interactions, authentication flows, and security design.

## System Overview

GreenLane is a microservice-oriented maritime emissions tracking platform composed of five primary Docker services orchestrated by Docker Compose. All services communicate over an internal Docker network, with nginx acting as the external reverse proxy and SSL termination point.

```
┌─────────────┐     ┌─────────────────────────────────────────────┐     ┌──────────────┐
│   Browser    │────▶│              nginx (Port 80/443)             │────▶│              │
│  (React SPA) │     │  - SSL Termination / Rate Limiting          │     │   Backend    │
└─────────────┘     │  - Reverse Proxy to Backend & Frontend       │     │  (FastAPI)   │
                    │  - Static File Serving                       │     └──────┬───────┘
                    └──────────────────┬────────────────────────────┘            │
                                       │                                         │
                              ┌────────▼────────┐                                │
                              │   Frontend       │◀────────────────────────────────┘
                              │  (React + Nginx) │
                              └─────────────────┘
                                       │
                              ┌────────▼────────┐
                              │   Backend        │
                              │  (FastAPI)       │
                              │  Port 8000       │
                              └──┬──────┬────┬──┘
                                 │      │    │
                    ┌────────────┤      │    └────────────┐
                    │            │      │                 │
              ┌─────▼────┐ ┌────▼────┐ ┌──▼────────┐ ┌───▼──────┐
              │ MongoDB  │ │  Redis  │ │ Celery    │ │  Audit   │
              │ (Data)   │ │(Blacklist)│ (Tasks)  │ │ Logs     │
              └──────────┘ └─────────┘ └───────────┘ └──────────┘
```

### Service Descriptions

| Service   | Image         | Port  | Role                                                    |
|-----------|---------------|-------|---------------------------------------------------------|
| nginx     | nginx:alpine  | 80/443| Reverse proxy, SSL termination, rate limiting, static file serving |
| backend   | python:3.12-slim | 8000 | FastAPI application handling all API requests          |
| frontend  | node:20-alpine + nginx:alpine | 5173 | React SPA built with Vite, served by nginx          |
| mongo     | mongo:7       | 27017 | MongoDB database for all persistent data (internal only) |
| redis     | redis:7-alpine| 6379  | Token blacklist for session management                  |
| celery  | python:3.12-slim | —   | Background task worker for report generation            |

## Technology Stack

### Backend

- **FastAPI** — Modern async web framework with automatic OpenAPI documentation
- **Motor** — Async MongoDB driver for non-blocking database operations
- **Pydantic** — Data validation and serialization with Pydantic v2 models
- **Pydantic-Settings** — Environment-based configuration management
- **python-jose** — JWT token creation and verification (HS256 algorithm)
- **Passlib** — Password hashing with bcrypt
- **SlowAPI** — Rate limiting middleware
- **Celery** — Background task queue for report generation
- **Redis** — Token blacklist storage with automatic TTL expiration
- **Prometheus Client** — Metrics instrumentation

### Frontend

- **React** — UI component library (v18)
- **TypeScript** — Static type checking
- **Vite** — Build tool and development server
- **Zustand** — State management
- **React Router** — Client-side routing
- **Leaflet** — Map visualization for vessel tracking
- **Axios** — HTTP client with automatic token refresh interceptor

### Infrastructure

- **Docker Compose** — Service orchestration and container management
- **Nginx** — Reverse proxy, SSL termination, load balancing, rate limiting
- **MongoDB** — NoSQL database with replica set support
- **Redis** — In-memory data store for token blacklist

## Authentication Flow

GreenLane uses a JWT-based authentication system with Redis-backed token blacklist for secure session management.

### Login Flow

```
1. User submits email/password → POST /api/v1/auth/login
2. Backend verifies credentials against MongoDB (is_active check enforced)
3. Backend creates access token (15 min expiry) and refresh token (7 day expiry)
4. Access token returned in response body; refresh token set as httpOnly cookie
5. Frontend stores access token in memory
6. All subsequent API calls include Authorization: Bearer <access_token>
```

### Token Refresh Flow

```
1. Access token expires → Frontend receives 401 response
2. Axios interceptor automatically calls refreshToken()
3. POST /api/v1/auth/refresh sends refresh_token via httpOnly cookie
4. Backend verifies refresh token against Redis blacklist (must not be blacklisted)
5. Backend validates org_id in token payload matches user record
6. Old refresh token is blacklisted in Redis
7. New access token and new refresh token are issued
8. New refresh token set as httpOnly cookie
```

### Logout Flow

```
1. POST /api/v1/auth/logout
2. Backend retrieves refresh_token from cookie
3. Both access token and refresh token are added to Redis blacklist with TTL
4. Refresh token cookie is deleted
5. Blacklisted tokens cannot be used for any subsequent requests
```

### Multi-Tenancy (org_id)

Every user belongs to an organization identified by `org_id`. All database queries filter by `org_id` to ensure tenant isolation:

- Users can only access ships, voyages, and emissions within their `org_id`
- The `require_role` decorator checks both JWT role and database role
- `get_current_tenant_user` verifies `is_active: True` and fetches role from database
- Invited users always receive the `Operator` role; only org creators are `Org Admin`
- Dashboard and emissions endpoints always filter by `org_id` to prevent cross-tenant data leakage

## Emissions Calculation (IMO DCS)

The platform calculates greenhouse gas emissions using the IMO Data Collection System (DCS) methodology.

### Calculation Process

1. **Voyage Created** — When a voyage is logged, `calculate_voyage_emissions()` computes emissions based on:
   - Fuel type (HFO, MGO, LNG, Methanol)
   - Fuel consumed (metric tonnes)
   - Distance traveled (nautical miles)
   - Cargo carried (metric tonnes)

2. **Emissions Record Built** — `build_emissions_record()` creates a complete record containing:
   - CO2, CH4, N2O, SOX, NOX emissions in tonnes
   - CO2 equivalent (total greenhouse gas impact)
   - Calculation version (enables history tracking)
   - `is_current` flag for the latest calculation

3. **Versioned Records** — When a voyage is updated, previous emissions are marked `is_current=False` and a new version is inserted. This creates an auditable calculation history.

4. **Aggregation** — The `/emissions/summary` endpoint uses MongoDB aggregation pipelines to compute totals by fuel type, pollutant, and vessel.

### IMO Emission Factors

Emission factors are applied based on fuel type. The `emissions_calculator.py` module implements the standard IMO DCS calculation formulas for each fuel category.

## Report Generation Flow

Reports are generated asynchronously using Celery background tasks to avoid blocking the API.

```
1. User POSTs /api/v1/reports/generate with target year
2. Backend validates request, fetches ships/voyages/emissions for the org
3. Creates report document in MongoDB with status "Queued"
4. Celery task generate_report_task.delay() is called with all data
5. Background worker generates IMO DCS Annual Compliance Report PDF
6. PDF is saved to reports_storage/
7. Report status updated to "Generated"
8. User can download via GET /api/v1/reports/{id}/download
```

### Report Lifecycle

- **Queued** — Task submitted to Celery
- **Generated** — PDF report created and saved
- **Submitted** — Report submitted to regulatory body (manual)

Status transitions are managed via `PATCH /api/v1/reports/{id}/status` (requires Compliance Officer or Org Admin role).

## Docker Services and Their Roles

### nginx

- Listens on ports 80 (HTTP redirect to HTTPS) and 443 (HTTPS)
- Terminates TLS with certificates from `certs/` directory
- Rate limits API endpoints (10r/s burst 20) and general traffic (100r/s burst 50)
- Proxies `/api/v1/` to backend and `/assets/` to frontend
- Serves health check requests directly without rate limiting
- Sets security headers (HSTS, CSP, X-Content-Type-Options, etc.)
- Uses JSON-formatted access logging

### backend (FastAPI)

- Main application server running Uvicorn on port 8000
- Contains all API routers: auth, fleet, emissions, reports, dashboard
- Global exception handlers for `RequestValidationError` and generic exceptions
- Security headers middleware with CSP, HSTS, and XSS protection
- SlowAPI rate limiting on all endpoints
- Database connection pool with 50 max connections, 10 min connections
- Automatically initializes MongoDB indexes on startup via lifespan

### celery

- Background worker process consuming from Celery task queue
- Runs `generate_report_task` for asynchronous report PDF generation
- Shares the same Python environment and configuration as backend
- Depends on backend being healthy (starts after backend)

### mongo

- MongoDB 7 with `--auth` enabled (requires authentication)
- Persistent volume `mongo_data` for data durability
- Health check via `mongosh` ping command
- No host port exposed — only accessible via internal Docker network
- Connection pool: 50 max, 10 min, 10s timeout, 30s socket timeout
- `w="majority"`, `j=True` for write concern
- Replica set `rs0` configured for future scaling

### redis

- Redis 7 Alpine with append-only file persistence
- Used for token blacklist (logout invalidation, refresh token rotation)
- Blacklist entries have TTL matching token expiry
- Internal only, no host port exposed

## Security Architecture

### Defense in Depth

GreenLane implements multiple layers of security:

1. **Network Security** — MongoDB and Redis are not exposed to the host; only nginx and backend are publicly accessible
2. **TLS Termination** — All traffic between client and nginx is encrypted; internal traffic uses Docker's encrypted network
3. **Authentication** — JWT tokens with short expiry (15 min) + refresh tokens (7 days); Redis-backed blacklist ensures immediate revocation
4. **Authorization** — Role-based access control with `require_role` decorator; database-level role verification prevents stale JWT privilege escalation
5. **Multi-Tenancy** — Every query filters by `org_id`; cross-tenant data access is structurally impossible
6. **Input Validation** — All request bodies validated by Pydantic models; enum fields restrict to allowed values
7. **Rate Limiting** — SlowAPI rate limits on all endpoints (5/min for auth, varying by endpoint)
8. **Security Headers** — CSP, HSTS, X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy
9. **Cookie Security** — Refresh tokens in httpOnly, Secure, SameSite=Strict cookies; access tokens in JS memory (HttpOnly cookie consideration documented as P2)
10. **Audit Logging** — All mutations logged to `audit_logs` collection with 1-year TTL

### Known Limitations (P2)

The following security improvements are documented as future work:
- In-memory token blacklist → Redis-backed (already implemented; further testing needed)
- Access tokens in HttpOnly cookies instead of JS memory
- CSRF protection via double-submit cookie pattern
- Structured JSON logging middleware
- Prometheus `/metrics` endpoint (documented in monitoring)
- CI/CD pipeline configuration
