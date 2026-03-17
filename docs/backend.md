# Backend

## Overview

The API server (`/apiserver`) is a Django 4.2 application using Django REST Framework. It serves as the single source of truth for all data and business logic.

## Directory Structure

```
apiserver/
├── plane/
│   ├── api/                # REST API views, serializers, URL routing
│   │   ├── views/          # ViewSets and APIViews
│   │   ├── serializers/    # DRF serializers
│   │   └── urls/           # URL configuration
│   ├── app/                # Django apps with models and migrations
│   ├── authentication/     # Auth providers (OAuth, credentials, magic link)
│   │   └── provider/       # GitHub, Google OAuth implementations
│   ├── bgtasks/            # Celery background tasks
│   ├── db/                 # Database models
│   │   └── models/         # Django ORM model definitions
│   ├── middleware/          # Custom Django middleware
│   ├── license/            # License management
│   ├── settings/           # Django settings (base, local, production, test)
│   └── utils/              # Shared utilities
├── requirements/           # Python dependencies
│   ├── base.txt            # Core dependencies
│   ├── local.txt           # Development dependencies
│   ├── test.txt            # Testing dependencies
│   └── production.txt      # Production dependencies
├── templates/              # Email templates
├── bin/                    # Docker entrypoint scripts
└── manage.py               # Django management command entry point
```

## API Design

### Base Classes
All views extend `BaseAPIView` which provides:
- Pagination support
- User timezone handling
- Filter backends
- Rate limiting (throttle classes)

### URL Structure
Endpoints are namespaced under `/api/v1/` and organized by resource:

```
/api/v1/workspaces/{slug}/
    ├── projects/
    │   ├── {id}/issues/
    │   ├── {id}/cycles/
    │   ├── {id}/modules/
    │   ├── {id}/states/
    │   ├── {id}/labels/
    │   ├── {id}/pages/
    │   └── {id}/members/
    ├── members/
    └── integrations/
```

### Authentication
- `APIKeyAuthentication` — Token-based for external integrations
- Session authentication — For web app requests
- OAuth — GitHub, Google sign-in
- Magic links — Passwordless email-based

### Permissions
Custom DRF permission classes enforce role-based access:
- `ProjectEntityPermission` — Project-level resource access
- `ProjectMemberPermission` — Member-specific operations
- `WorkspacePermission` — Workspace-level access

### Rate Limiting
- `ApiKeyRateThrottle` — Limits for API key access
- `ServiceTokenRateThrottle` — Limits for service tokens

## Database Models

Core models live in `apiserver/plane/db/models/`:

| Model | Description |
|-------|-------------|
| `User` | Extended Django user model |
| `Workspace` | Top-level organization unit |
| `Project` | Project within a workspace |
| `Issue` | Core work item |
| `Cycle` | Sprint/iteration container |
| `Module` | Feature/milestone grouping |
| `State` | Workflow states (Todo, In Progress, Done, etc.) |
| `Label` | Categorization tags |
| `Page` | Rich text documents |
| `View` | Saved filter configurations |
| `Notification` | In-app notifications |
| `Webhook` | Event-driven integrations |
| `FileAsset` | Uploaded file references |

All models include `created_at`, `updated_at` audit fields.

## Background Tasks

Celery tasks in `apiserver/plane/bgtasks/` handle:
- Email notifications (issue updates, mentions, invitations)
- Webhook event delivery
- Analytics computation
- Data exports (XLSX via openpyxl)
- Integration syncs (GitHub, Slack)
- Scheduled tasks via Celery Beat

## Settings

Django settings are split by environment:
- `base.py` — Shared configuration
- `local.py` — Development overrides
- `production.py` — Production settings (Sentry, caching)
- `test.py` — Test-specific configuration

## Python Dependencies

| Package | Purpose |
|---------|---------|
| `django` 4.2 | Web framework |
| `djangorestframework` 3.15 | REST API toolkit |
| `celery` 5.4 | Async task queue |
| `redis` 5.0 | Cache and session backend |
| `psycopg` | PostgreSQL adapter |
| `boto3` / `minio` | S3-compatible object storage |
| `openai` 1.25 | AI features |
| `slack-sdk` 3.27 | Slack integration |
| `sentry-sdk` | Error tracking |
| `openpyxl` 3.1 | Excel export |
| `cryptography` | Token signing and encryption |

## Code Quality

- **Linter**: Ruff (pycodestyle + pyflakes + isort + McCabe)
- **Line length**: 88 (Black-compatible)
- **String quotes**: Double quotes
- **Complexity limits**: McCabe max 10, max function args 8
