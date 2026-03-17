# Frontend

## Overview

The frontend consists of three Next.js 14 applications (`web`, `admin`, `space`) sharing code through monorepo packages. All use React 18, TypeScript 5.3, and Tailwind CSS 3.3.

## Applications

### Web (`/web`)
The main application with full project management capabilities.

**Directory structure:**
```
web/
├── app/                    # Next.js App Router pages
│   └── [workspaceSlug]/    # Workspace-scoped routes
│       ├── projects/       # Project pages
│       ├── settings/       # Workspace settings
│       └── ...
├── core/                   # Core business logic
│   ├── components/         # React components (organized by feature)
│   ├── hooks/              # Custom React hooks
│   ├── services/           # API client service classes
│   ├── store/              # MobX state stores
│   ├── layouts/            # Page layouts
│   └── lib/                # Helper libraries
├── ce/                     # Community Edition code
├── ee/                     # Enterprise Edition code
├── helpers/                # Utility helper functions
└── styles/                 # Global CSS styles
```

### Admin (`/admin`)
Lighter application for instance administration.

### Space (`/space`)
Public-facing app for external sharing.

## State Management

MobX is used for client-side state. Stores are organized by domain in `web/core/store/`:

- `issue/` — Issue CRUD, filters, ordering
- `cycle/` — Sprint/cycle management
- `module/` — Module tracking
- `project/` — Project settings and members
- `user/` — Current user and preferences
- `workspace/` — Workspace configuration

Stores are accessed via React context and custom hooks.

## Component Patterns

- Components are organized by feature domain under `web/core/components/`
- Shared UI primitives live in `packages/ui/src/`
- The rich text editor is in `packages/editor/src/` (Tiptap/Prosemirror)
- Drag-and-drop uses Atlaskit Pragmatic DnD

## API Communication

Service classes in `web/core/services/` wrap Axios calls to the Django API:

```typescript
// Example: web/core/services/issue.service.ts
class IssueService extends APIService {
  async getIssues(workspaceSlug: string, projectId: string): Promise<IIssue[]> {
    return this.get(`/api/v1/workspaces/${workspaceSlug}/projects/${projectId}/issues/`);
  }
}
```

## Styling

- Tailwind CSS with custom configuration (`packages/tailwind-config-custom/`)
- Global styles in `web/styles/`
- Component-level Tailwind classes (no CSS modules)

## Path Aliases

Each app has TypeScript path aliases for clean imports:
- `@/*` — App root
- `@/helpers/*` — Helper functions
- `@/plane-web/*` — Web-specific modules (in `web/`)

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `next` 14.2 | React framework (App Router) |
| `react` 18.3 | UI library |
| `mobx` 6.10 | State management |
| `axios` 1.7 | HTTP client |
| `tailwindcss` 3.3 | Utility-first CSS |
| `@tiptap/*` | Rich text editor |
| `lucide-react` | Icon library |
| `react-hook-form` 7.51 | Form handling |
| `@nivo/*` | Data visualization charts |
| `posthog-js` | Product analytics |
