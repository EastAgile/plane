# Architecture

## Overview

Plane is a monorepo containing multiple frontend applications, a Django REST API backend, a real-time collaboration server, and shared packages. Services communicate over HTTP (REST) and WebSockets, orchestrated behind an Nginx reverse proxy.

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Nginx (Reverse Proxy)                     │
│                           Port 9999                              │
├──────────┬──────────┬──────────┬──────────┬─────────────────────┤
│  Web     │  Admin   │  Space   │  Live    │  API Server         │
│  :3000   │  :3001   │          │  (WS)    │  :8000              │
│  Next.js │  Next.js │  Next.js │  Express │  Django + DRF       │
├──────────┴──────────┴──────────┴──────────┴─────────────────────┤
│                        Infrastructure                            │
├──────────┬──────────┬──────────┬──────────┬─────────────────────┤
│ Postgres │  Redis   │ RabbitMQ │  MinIO   │  Celery Workers     │
│  :5432   │  :6379   │  :5672   │  :9000   │                     │
└──────────┴──────────┴──────────┴──────────┴─────────────────────┘
```

## Services

### Web (`/web`)
The primary user-facing application. Built with Next.js 14 using the App Router. Manages issues, cycles, modules, views, pages, dashboards, and analytics. State management via MobX stores.

### Admin (`/admin`)
Instance administration dashboard. Used for managing workspace settings, authentication providers, and system configuration.

### Space (`/space`)
Public-facing application for sharing issues and project boards with external stakeholders. Read-only or limited-access views.

### Live (`/live`)
Real-time collaboration server built on Express.js with HocusPocus (Yjs). Powers collaborative document editing in Pages with conflict-free replicated data types (CRDTs). Communicates with clients via WebSocket and syncs state through Redis.

### API Server (`/apiserver`)
Django REST Framework backend. Handles all business logic, data persistence, authentication, authorization, file uploads, webhooks, and integrations. Exposes REST endpoints under `/api/v1/`.

### Celery Workers
Background task processing via Celery with RabbitMQ as the message broker. Handles email notifications, webhook deliveries, analytics computation, issue exports, and other async operations.

## Data Flow

### Standard Request
```
Browser → Nginx → Next.js (SSR/CSR) → Axios → Django API → PostgreSQL
                                                         → Redis (cache)
```

### Real-time Collaboration
```
Browser → WebSocket → Nginx → Live Server (HocusPocus)
                                    ↕ Redis (pub/sub)
                                    ↕ Django API (persistence)
```

### Background Processing
```
Django API → RabbitMQ → Celery Worker → PostgreSQL/Redis/S3
                                      → External APIs (Slack, GitHub, Email)
```

## Database Schema (Key Entities)

```
Workspace
  ├── Project
  │     ├── Issue
  │     │     ├── IssueComment
  │     │     ├── IssueAssignee
  │     │     ├── IssueLabel
  │     │     ├── IssueReaction
  │     │     └── IssueRelation
  │     ├── Cycle → CycleIssue
  │     ├── Module → ModuleIssue
  │     ├── State
  │     ├── Label
  │     ├── Page
  │     └── View
  ├── WorkspaceMember
  └── Integration (GitHub, Slack)
```

## Authentication

Multiple authentication strategies are supported:
- **OAuth**: GitHub and Google providers
- **API Keys**: Token-based programmatic access
- **Session**: Django session cookies for web apps
- **Magic Links**: Passwordless email-based login

Role-based access control is enforced at workspace and project levels (Owner, Admin, Member, Guest).
