# SAHAY — Mental Health Platform (Counsellor Dashboard)

## Overview
SAHAY is a privacy-preserving mental health support platform designed for counsellor workflows. It uses wearable-derived signals to surface alerts, explanations, and structured intervention tools while keeping the system non-diagnostic.

## Prerequisites
- Docker Engine 24+
- Docker Compose v2+
- (Optional) `make` if using the Makefile targets

## Quick Start (Production)

1. Copy `.env.example` to `.env` and set production values:
```bash
cp .env.example .env
```

2. Build and start all services:
```bash
docker compose up -d --build
```

3. Verify health:
```bash
curl http://localhost/api/v1/health
# Expected: {"status":"ok","backend":"connected","database":"connected"}
```

4. Open the counsellor dashboard:
```
http://localhost/
```

## Service Architecture

| Service | Image | Port | Description |
|---------|-------|------|-------------|
| `db` | `postgres:16-alpine` | 5432 (internal) | PostgreSQL with persistent volume |
| `api` | Built from `services/api/Dockerfile` | 8000 (internal) | FastAPI backend with uvicorn |
| `web` | Built from `apps/web/Dockerfile` | 80 | Nginx serving React build |

## Environment Variables

See `.env.example` for all available variables. Key ones:

- `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` — Database credentials
- `DATABASE_URL` — SQLAlchemy async connection string
- `CORS_ORIGINS` — Comma-separated list of allowed origins
- `DEBUG` — Set to `false` in production
- `LOG_LEVEL` — Python logging level (`INFO`, `WARNING`, `ERROR`)

## Database

- Data persists in the `postgres_data` Docker volume.
- Tables are created automatically on API startup via SQLAlchemy `create_all`.
- For production, back up the volume regularly:
```bash
docker compose exec db pg_dump -U sahay sahay > backup.sql
```

## Health Checks

- **Backend**: `GET /api/v1/health`
- **Frontend**: `GET /health` (returns `ok`)
- **Database**: `pg_isready` inside the `db` container

Docker Compose uses these to enforce startup order.

## Logs

```bash
# All services
docker compose logs -f

# Backend only
docker compose logs -f api

# Frontend only
docker compose logs -f web
```

## Common Commands

```bash
# Stop services
docker compose down

# Stop and remove volumes (WARNING: deletes database data)
docker compose down -v

# Rebuild after code changes
docker compose up -d --build

# Run backend tests locally
cd services/api && python -m pytest tests/ -v

# Run frontend typecheck locally
cd apps/web && npx tsc --noEmit

# Frontend production build locally
cd apps/web && npm run build
```

## Security Notes

- Never commit `.env` to version control.
- Rotate `POSTGRES_PASSWORD` before first production deployment.
- Keep the system non-diagnostic: the platform surfaces risk signals for counsellor review, not medical diagnosis.
- Consent, RBAC, and audit logging are preserved across all phases.
