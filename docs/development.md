# Development

## Prerequisites

- Node.js (for frontend apps)
- Yarn 1.22 (package manager)
- Python 3.12 (for API server)
- Docker & Docker Compose (for infrastructure services)
- Git

## Quick Start with Docker

The fastest way to get everything running:

```bash
# 1. Clone and setup
git clone <repo-url>
cd plane
./setup.sh                  # Copies .env.example files, generates SECRET_KEY

# 2. Start all services
docker compose -f docker-compose-local.yml up -d

# 3. Access
# Web:   http://localhost:3000
# Admin: http://localhost:3001
# API:   http://localhost:8000
```

## Frontend Development

```bash
# Install dependencies
yarn install

# Start all frontend apps with hot reload
yarn dev

# Build all packages and apps
yarn build

# Lint
yarn lint

# Format with Prettier
yarn format
```

### Running Individual Apps

```bash
# Web app only
cd web && yarn dev

# Admin app only
cd admin && yarn develop

# Space app only
cd space && yarn dev
```

## Backend Development

```bash
cd apiserver

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements/local.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver 0.0.0.0:8000
```

### Running Celery Workers

```bash
cd apiserver
celery -A plane worker -l info
celery -A plane beat -l info    # For scheduled tasks
```

## Linting & Formatting

### Frontend
```bash
yarn lint              # ESLint across all packages
yarn lint:errors       # Errors only (no warnings)
yarn format            # Prettier formatting
```

### Backend
```bash
cd apiserver
ruff check .           # Lint Python code
ruff format .          # Format Python code
```

## Git Workflow

- Default branch: `ea_main`
- Create feature branches from `ea_main`
- Open PRs targeting `ea_main`
- CI runs on pull requests via GitHub Actions

## Environment Variables

Each service has its own `.env.example` file:
- Root `.env` — Database, Redis, S3 credentials
- `apiserver/.env` — Django settings, API keys
- `web/.env` — Public frontend config (API URLs, analytics keys)
- `admin/.env` — Admin app config
- `space/.env` — Space app config
- `live/.env` — Live server config

Copy them and fill in values:
```bash
cp .env.example .env
cp apiserver/.env.example apiserver/.env
cp web/.env.example web/.env
# ... etc
```

## Turbo

Turbo orchestrates builds, tests, and dev servers across the monorepo:

```bash
turbo run build          # Build with dependency graph
turbo run dev            # Dev servers for all apps
turbo run lint           # Lint all packages
turbo run test           # Test all packages
```

Build outputs are cached in `.turbo/` directories.

## Docker Services (Local)

| Service | Image | Port |
|---------|-------|------|
| web | plane-web | 3000 |
| admin | plane-admin | 3001 |
| api | plane-backend | 8000 |
| worker | plane-backend | — |
| beat-worker | plane-backend | — |
| live | plane-live | — |
| postgres | postgres:15.7 | 5432 |
| redis | valkey:7.2.5 | 6379 |
| rabbitmq | rabbitmq:3.13.6 | 5672 |
| minio | minio | 9000 |
| nginx | plane-proxy | 9999 |
