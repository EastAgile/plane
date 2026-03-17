# Shared Packages

## Overview

Shared code lives in `packages/` and is consumed by the frontend applications via Yarn workspaces and Turbo build orchestration.

## Packages

### `@plane/ui` (`packages/ui/`)
Shared React UI component library. Contains buttons, inputs, modals, dropdowns, tooltips, and other primitives used across all frontend apps.

### `@plane/editor` (`packages/editor/`)
Rich text editor built on Tiptap (Prosemirror). Supports:
- Collaborative editing via Yjs
- Slash commands
- Mentions
- Image/file embeds
- Markdown shortcuts
- AI-assisted writing

### `@plane/types` (`packages/types/`)
TypeScript type definitions shared across all frontend apps. Defines interfaces for API responses, store shapes, and component props.

### `@plane/hooks` (`packages/hooks/`)
Reusable custom React hooks shared across apps (e.g., debounce, outside click, intersection observer).

### `@plane/utils` (`packages/utils/`)
Shared utility functions (date formatting, string manipulation, etc.).

### `@plane/constants` (`packages/constants/`)
Shared constants (API routes, feature flags, default values, enums).

### Configuration Packages

| Package | Path | Purpose |
|---------|------|---------|
| `@plane/typescript-config` | `packages/typescript-config/` | Base tsconfig for all apps |
| `@plane/eslint-config` | `packages/eslint-config/` | Shared ESLint rules |
| `@plane/tailwind-config-custom` | `packages/tailwind-config-custom/` | Shared Tailwind theme and plugins |

## Build Order

Turbo manages the build dependency graph. Packages are built before the apps that depend on them:

```
typescript-config ─┐
eslint-config     ─┤
tailwind-config   ─┼→ ui ─┐
types             ─┤      ├→ web / admin / space
utils             ─┤      │
hooks             ─┤      │
constants         ─┘      │
editor ───────────────────┘
```

## Adding a New Package

1. Create directory under `packages/`
2. Add `package.json` with `@plane/` namespace
3. Reference it in the consuming app's `package.json`
4. Add build configuration to `turbo.json` if needed
5. Run `yarn install` to link workspaces
