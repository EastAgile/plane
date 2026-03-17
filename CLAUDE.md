# Plane - Project Management Platform

Open-source project management tool built with Next.js frontends and a Django REST API backend. This is the EastAgile fork with self-hosting and Pivotal Tracker migration support.

## Repository Structure

Turbo-based monorepo with Yarn workspaces:

- `web/` — Main web app (Next.js 14, React 18, MobX, Tailwind CSS)
- `admin/` — Admin dashboard (Next.js)
- `space/` — Public issue viewer (Next.js)
- `live/` — Real-time collaboration server (Node.js, Express, HocusPocus/Yjs)
- `apiserver/` — Django REST API backend (Python 3.12, Django 4.2, DRF)
- `packages/` — Shared packages (ui, editor, hooks, types, utils, constants, configs)
- `deploy/` — Deployment configs (Docker, self-hosting)
- `nginx/` — Reverse proxy configuration

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, TypeScript 5.3, Tailwind CSS 3.3 |
| State | MobX 6.10 |
| Editor | Tiptap (Prosemirror) via @plane/editor |
| Backend | Python 3.12, Django 4.2, Django REST Framework |
| Database | PostgreSQL 15 |
| Cache | Redis (Valkey 7.2 in production) |
| Queue | Celery 5.4 + RabbitMQ |
| Real-time | HocusPocus 2.11 + Yjs |
| Storage | S3 / MinIO |

## Default Branch

The default branch is `ea_main`. Base all new branches and PRs on `ea_main`.

## Development

### Quick Start (Docker)
```bash
./setup.sh                                        # Copy env files, generate SECRET_KEY
docker compose -f docker-compose-local.yml up -d  # Start all services
# Access at http://localhost:9999 (Nginx proxy)
```

### Frontend Development
```bash
yarn install          # Install dependencies (Yarn 1.22)
yarn dev              # Run all frontend apps via Turbo (concurrency=13)
yarn build            # Build all packages
yarn lint             # Lint all packages
yarn format           # Prettier formatting
```

### Backend Development
```bash
cd apiserver
pip install -r requirements/local.txt
python manage.py migrate
python manage.py runserver
```

## Code Conventions

### TypeScript / JavaScript
- **Linter**: ESLint with `@plane/eslint-config`
- **Formatter**: Prettier (printWidth: 120, trailing commas: es5, 2 spaces)
- **Path aliases**: `@/*` for imports within each app
- **Types**: Shared via `@plane/types` package

### Python
- **Linter/Formatter**: Ruff (Black-compatible, line length 88)
- **Quotes**: Double quotes
- **Imports**: isort-compatible ordering
- **Complexity**: McCabe max 10, max args 8, max statements 50

### General
- Community Edition code in `ce/` directories, Enterprise in `ee/`
- API endpoints follow REST conventions under `/api/v1/`
- MobX stores in `web/core/store/`
- React components in `web/core/components/`
- API service classes in `web/core/services/`

## Architecture

```
Browser → Nginx → Next.js (Web/Admin/Space)
                       ↓ Axios
                  Django REST API (:8000)
                       ↓
                  PostgreSQL + Redis

Real-time: Browser → WebSocket → Live Server ← Redis
Background: API → Celery → RabbitMQ → Workers
```

## Key Directories

| Path | Purpose |
|------|---------|
| `web/core/components/` | React UI components |
| `web/core/store/` | MobX state stores |
| `web/core/services/` | API client services |
| `web/core/hooks/` | Custom React hooks |
| `packages/ui/src/` | Shared UI component library |
| `packages/editor/src/` | Rich text editor package |
| `apiserver/plane/api/` | REST API views and serializers |
| `apiserver/plane/db/models/` | Django database models |
| `apiserver/plane/bgtasks/` | Celery background tasks |

## Testing

- Frontend: ESLint + TypeScript type checking
- Backend: pytest (`apiserver/requirements/test.txt`)
- CI: GitHub Actions (`.github/workflows/`)

## Docker Services

| Service | Port | Description |
|---------|------|-------------|
| web | 3000 | Main web application |
| admin | 3001 | Admin dashboard |
| api | 8000 | Django REST API |
| live | — | Real-time collaboration |
| nginx | 9999 | Reverse proxy |
| postgres | 5432 | Database |
| redis | 6379 | Cache & sessions |
| rabbitmq | 5672 | Message queue |
| minio | 9000 | Object storage |
