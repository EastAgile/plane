# Development

## Prerequisites

- **Docker Desktop** — Required for running the full stack locally
- **Yarn 1.22** — JavaScript package manager (install via `brew install yarn`)
- **Node.js 18+** — For frontend development
- **Git**

### Installing Prerequisites (macOS)

```bash
# Install Yarn
brew install yarn

# Install Docker Desktop
brew install --cask docker

# Launch Docker Desktop (required before first use)
open /Applications/Docker.app

# Link Docker Compose CLI plugin (if `docker compose` doesn't work)
mkdir -p ~/.docker/cli-plugins
ln -sf /Applications/Docker.app/Contents/Resources/cli-plugins/docker-compose ~/.docker/cli-plugins/docker-compose
```

## Quick Start with Docker

The fastest way to get everything running:

```bash
# 1. Clone and setup
git clone <repo-url>
cd plane
./setup.sh                  # Copies .env.example files, generates SECRET_KEY

# 2. Start all services (first run builds images, takes a few minutes)
docker compose -f docker-compose-local.yml up -d

# 3. Wait for migrations and API startup
docker compose -f docker-compose-local.yml logs -f migrator  # Watch migrations
docker compose -f docker-compose-local.yml logs -f api       # Watch API startup

# 4. Access via Nginx proxy
# All services: http://localhost:9999
```

> **Note**: All services are accessed through the Nginx proxy on port 9999.
> The proxy routes to the correct internal service based on the URL path.

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

| Service | Image | Internal Port | Description |
|---------|-------|---------------|-------------|
| web | plane-web | 3000 | Main web application |
| admin | plane-admin | 3000 | Admin dashboard |
| space | plane-space | 4000 | Public issue viewer |
| live | plane-live | 3003 | Real-time collaboration |
| api | plane-api | 8000 | Django REST API |
| worker | plane-worker | — | Celery worker |
| beat-worker | plane-beat-worker | — | Celery beat scheduler |
| migrator | plane-migrator | — | Runs DB migrations then exits |
| plane-db | postgres:15.7-alpine | 5432 | PostgreSQL database |
| plane-redis | valkey:7.2.5-alpine | 6379 | Redis cache |
| plane-mq | rabbitmq:3.13.6 | 5672 | RabbitMQ message queue |
| plane-minio | minio/minio | 9000 | S3-compatible object storage |
| proxy | plane-proxy | 80 → **9999** | Nginx reverse proxy (only exposed port) |

### Useful Docker Commands

```bash
# Check all service status
docker compose -f docker-compose-local.yml ps

# View logs for a specific service
docker compose -f docker-compose-local.yml logs -f web
docker compose -f docker-compose-local.yml logs -f api

# Restart a single service
docker compose -f docker-compose-local.yml restart api

# Stop all services
docker compose -f docker-compose-local.yml down

# Stop and remove volumes (reset database)
docker compose -f docker-compose-local.yml down -v

# Rebuild images after code changes to Dockerfiles
docker compose -f docker-compose-local.yml up -d --build
```
