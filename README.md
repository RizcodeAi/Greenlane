# GreenLane Maritime MVP

[![CI](https://github.com/greenlane/greenlane/actions/workflows/ci.yml/badge.svg)](https://github.com/greenlane/greenlane/actions/workflows/ci.yml)
[![Security](https://img.shields.io/badge/Security-Audited-blue)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

**GreenLane Maritime** — A production-ready B2B SaaS emissions compliance platform for shipping companies. Built for IMO Data Collection System (DCS) compliance under MARPOL Annex VI.

## Features

- **Fleet Management** — Add, edit, and manage vessels with IMO numbers and compliance status
- **Voyage Logging** — Track voyages with fuel consumption, distance, and cargo data
- **Emissions Engine** — Real-time IMO DCS-compliant emissions calculations (CO2, CH4, N2O, SOx, NOx)
- **EEOI Calculation** — Efficiency Indicator (g-CO2 / tonne-mile) for each voyage
- **IMO DCS Reports** — Generate official PDF compliance reports
- **Multi-Tenant RBAC** — Organization-level data isolation with role-based access control
- **Dashboard & Map** — Real-time fleet visualization with Leaflet maps
- **Audit Logging** — Append-only, TTL-backed audit trail

## Architecture

```
┌─────────────────────────────────────────────┐
│                  Frontend                     │
│         React 18 + Vite + TypeScript         │
│         Tailwind CSS + Zustand + Leaflet     │
└──────────────────┬──────────────────────────┘
                   │ HTTPS (nginx)
                   ▼
┌─────────────────────────────────────────────┐
│                  Backend                      │
│         FastAPI + Motor (Async MongoDB)      │
│         JWT Auth + Rate Limiting + CSP       │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│               MongoDB Atlas                   │
│         Replica Set + TLS + Auth             │
└─────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

### Development (without Docker)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your MongoDB URL and secrets
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### Docker Compose (Recommended)

```bash
make up
```

This starts MongoDB (with auth), the FastAPI backend, and nginx (SSL termination).

### Running Tests

```bash
make test-backend
make test-frontend
```

## Project Structure

```
greenlane/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # API routers (auth, fleet, emissions, reports, dashboard)
│   │   ├── core/             # Security, database, config, logging
│   │   ├── services/         # Business logic (emissions calculator, report generator, audit)
│   │   ├── models/           # Pydantic schemas
│   │   └── main.py           # FastAPI application entry point
│   ├── tests/                # pytest test suite
│   ├── Dockerfile
│   ├── requirements.txt
│   └── requirements.lock
├── frontend/
│   ├── src/
│   │   ├── components/       # React components (Navbar, Sidebar, Map, Modals)
│   │   ├── pages/            # Page components (Dashboard, Fleet, Voyages, Emissions, Reports)
│   │   ├── services/         # API service layer
│   │   ├── store/            # Zustand state management
│   │   └── App.tsx           # Main application
│   ├── Dockerfile
│   ├── package.json
│   └── vitest.config.ts
├── docker-compose.yml        # Full infrastructure with nginx, MongoDB
├── Dockerfile                # Root Dockerfile
├── Makefile                  # Convenience commands
├── SECURITY.md               # Vulnerability disclosure policy
└── AUDIT_REPORT.md           # Comprehensive security audit documentation
```

## Security

- All 4 audit passes completed (CTO, Principal Architect, Database Engineer, Security Engineer perspectives)
- 78 findings remediated across P0/P1 categories
- JWT access tokens stored in-memory only (never localStorage)
- Refresh tokens in `httpOnly`/`Secure`/`SameSite=Lax` cookies with server-side blacklisting
- Content-Security-Policy headers on all responses
- Organization-level data isolation enforced at application layer
- Append-only audit logging with TTL

## Regulatory Compliance

- IMO Data Collection System (DCS) fuel emission factors
- GWP100 CO2-equivalent calculations
- EEOI (Energy Efficiency Operational Indicator)
- Calculation versioning with `is_current` flag
- Audit trail for all emissions calculations

## License

MIT
"# Greenlane" 
