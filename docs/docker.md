# Docker Development & Production

MIDINecromancer includes Docker Compose configurations for both development and production environments with migration gating and hot reload support.

## Overview

The Docker setup uses **Compose profiles** to separate dev and prod environments:

- **Dev profile**: Hot reload, bind mounts, fast iteration
- **Prod profile**: Immutable images, static frontend, production server

Both profiles include:
- PostgreSQL database with persistent volume
- Migration gating (backend starts only after migrations succeed)
- Health checks and proper service dependencies

## Prerequisites

- Docker Engine 20.10+
- Docker Compose v2.0+
- `.env` file (copy from `.env.example`)

## Quick Start

### Development

```bash
# Start all dev services
make docker-dev
# or
docker compose --profile dev up --build
```

This starts:
1. **db**: PostgreSQL (healthy check)
2. **migrate-dev**: Runs Alembic migrations (one-shot)
3. **backend-dev**: FastAPI with hot reload (waits for migrations)
4. **frontend-dev**: Vite dev server (waits for backend)

Access:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Production

```bash
# Build and start production services
make docker-prod
# or
docker compose --profile prod up --build -d
```

This starts:
1. **db**: PostgreSQL
2. **migrate**: Runs migrations (one-shot)
3. **backend**: Gunicorn + Uvicorn workers (waits for migrations)
4. **frontend**: Nginx serving static assets (waits for backend)

Access:
- Frontend: http://localhost:80
- Backend API: http://localhost:8000

## Migration Gating

Both dev and prod profiles implement **migration gating**:

1. Database must be healthy (`service_healthy`)
2. Migration service must complete successfully (`service_completed_successfully`)
3. Backend starts only after both conditions are met

This ensures:
- No backend starts with outdated schema
- Migrations are idempotent (safe to run multiple times)
- Clear failure if migrations fail

### How It Works

```yaml
backend-dev:
  depends_on:
    db:
      condition: service_healthy
    migrate-dev:
      condition: service_completed_successfully
```

If migrations fail, `backend-dev` will not start, preventing schema mismatches.

## Development Profile

### Services

- **db**: PostgreSQL 16 Alpine
  - Port: 5432 (exposed for local tools)
  - Volume: `postgres_data` (persistent)
  - Health check: `pg_isready`

- **migrate-dev**: One-shot migration runner
  - Runs: `uv run alembic upgrade head`
  - Exits after completion
  - Source bind-mounted for live changes

- **backend-dev**: FastAPI with hot reload
  - Command: `uvicorn --reload`
  - Port: 8000
  - Source bind-mounted: `./backend:/app`
  - Auto-restarts on code changes

- **frontend-dev**: Vite dev server
  - Port: 5173
  - Source bind-mounted: `./frontend:/app`
  - Hot Module Replacement (HMR) enabled

### Hot Reload

Both backend and frontend support hot reload via bind mounts:

- **Backend**: Uvicorn `--reload` watches for Python file changes
- **Frontend**: Vite HMR watches for Vue/TypeScript changes

Edit files locally, see changes immediately in containers.

### Environment Variables

Set in `.env`:
```bash
POSTGRES_USER=midinecromancer
POSTGRES_PASSWORD=midinecromancer
POSTGRES_DB=midinecromancer
BACKEND_PORT=8000
FRONTEND_PORT=5173
DATABASE_URL=postgresql+asyncpg://midinecromancer:midinecromancer@db:5432/midinecromancer
```

## Production Profile

### Services

- **db**: Same PostgreSQL setup
  - Port: Not exposed (internal only)
  - Volume: `postgres_data`

- **migrate**: One-shot migration runner
  - Uses production backend image
  - Runs: `alembic upgrade head`
  - No source mounts

- **backend**: Production server
  - Gunicorn + 4 Uvicorn workers
  - Port: 8000 (internal, proxied by frontend)
  - No source mounts (immutable)
  - Health check enabled

- **frontend**: Static asset server
  - Nginx Alpine
  - Serves built `dist/` directory
  - SPA routing (history mode fallback)
  - Proxies `/api` to backend
  - Port: 80

### Build Process

Production images are built with:
- **Backend**: Non-editable install (`uv sync --no-dev`)
- **Frontend**: `npm run build` → static assets → nginx

No development dependencies or source code in production images.

## Dockerfiles

### Backend Dockerfile

Multi-stage with `dev` and `prod` targets:

**Dev target:**
- Installs uv
- `uv sync` (includes dev deps)
- Bind-mount friendly
- Runs `uvicorn --reload`

**Prod target:**
- `uv sync --no-dev` (production deps only)
- Non-editable install
- Gunicorn + Uvicorn workers
- Non-root user
- Health check

### Frontend Dockerfile

Multi-stage with `dev`, `build`, and `prod` targets:

**Dev target:**
- Node 20 Alpine
- `npm ci`
- Runs Vite dev server

**Build stage:**
- `npm run build`
- Outputs to `dist/`

**Prod target:**
- Nginx Alpine
- Serves `dist/`
- SPA routing config
- API proxy to backend

## Common Commands

### Development

```bash
# Start dev environment
make docker-dev

# View logs
make docker-logs
# or
docker compose --profile dev logs -f

# Stop services
make docker-down
# or
docker compose --profile dev down

# Clean volumes (removes database data)
make docker-clean
```

### Production

```bash
# Start production
make docker-prod

# View logs
docker compose --profile prod logs -f

# Stop services
docker compose --profile prod down

# Rebuild after code changes
docker compose --profile prod up --build -d
```

### Database

```bash
# Connect to database
docker compose exec db psql -U midinecromancer -d midinecromancer

# Run migrations manually (dev)
docker compose --profile dev run --rm migrate-dev

# Run migrations manually (prod)
docker compose --profile prod run --rm migrate
```

## Troubleshooting

### Migrations Fail

If migrations fail:
1. Check logs: `docker compose logs migrate-dev` (or `migrate`)
2. Backend will not start (by design)
3. Fix migration issues, then restart

### Backend Won't Start

Check dependencies:
```bash
# Is database healthy?
docker compose ps db

# Did migrations complete?
docker compose logs migrate-dev
```

### Port Conflicts

Change ports in `.env`:
```bash
BACKEND_PORT=8001
FRONTEND_PORT=5174
POSTGRES_PORT=5433
```

### Hot Reload Not Working

Ensure bind mounts are correct:
```bash
docker compose --profile dev config | grep volumes
```

Should show `./backend:/app` and `./frontend:/app`.

## Local Development Without Docker

Docker is optional. You can still run locally:

```bash
# Backend
cd backend
uv sync
uv run uvicorn midinecromancer.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

Just ensure PostgreSQL is running (via Docker or local install).

## Best Practices

1. **Use `.env` file**: Never commit secrets
2. **Check migrations**: Always verify migrations complete before backend starts
3. **Rebuild after dependency changes**: Run `--build` when `pyproject.toml` or `package.json` change
4. **Clean volumes carefully**: `docker-clean` removes database data
5. **Use health checks**: Services wait for dependencies to be healthy

## Production Deployment

For production deployment:

1. Set strong passwords in `.env`
2. Use secrets management (Docker secrets, env files, etc.)
3. Configure CORS origins properly
4. Set `ENVIRONMENT=production` and `DEBUG=false`
5. Use reverse proxy (nginx/traefik) in front of compose services
6. Enable SSL/TLS
7. Set resource limits in compose file
8. Use Docker secrets for sensitive data

## Image Sizes

Approximate sizes:
- **backend-dev**: ~500MB (includes dev tools)
- **backend-prod**: ~200MB (production only)
- **frontend-dev**: ~200MB (Node + dependencies)
- **frontend-prod**: ~50MB (nginx + static assets)

Production images are optimized for size and security.

