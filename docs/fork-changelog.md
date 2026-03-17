# Fork Changelog

This document tracks the changes made in the EastAgile fork compared to the upstream [makeplane/plane](https://github.com/makeplane/plane) repository, and the significant upstream changes since the fork point.

## Fork Details

| | |
|---|---|
| **Upstream** | `makeplane/plane` (branch: `preview`) |
| **Fork** | `EastAgile/plane` (branch: `ea_main`) |
| **Fork point** | Commit `9ed4591edc` — Dec 10, 2024 (upstream v0.24.1) |
| **EA commits since fork** | 40 |
| **Upstream commits since fork** | 1,749 |
| **EA files changed** | 128 files (+4,808 / -372 lines) |
| **Upstream files changed** | 7,807 files (+433,502 / -245,863 lines) |
| **Last updated** | March 17, 2026 |

---

## EastAgile Changes (our fork)

### Pivotal Tracker-like Customizations

These changes customize Plane to behave more like Pivotal Tracker for EastAgile's workflow:

| Feature ID | Date | Description |
|------------|------|-------------|
| [f] 001 | 2025-03-04 | Modify project point system from 1-6 to 0-3 scale |
| [f] 002 | 2025-03-04 | Rename "Unscheduled" state to "Icebox" and add "Backlog" stage |
| [f] 003 | 2025-03-07 | Implement automatic cycle creation and issue transfer |
| [f] 004 | 2025-03-07 | Automatic transfer of unfinished issues to next cycle |
| [f] 005 | 2025-03-04 | Remove cycle date edit restrictions |
| [f] 006 | 2025-03-05 | Remove "Upgrade" button for Plane pro from the UI |
| [f] 014 | 2025-03-05 | Apply default "Feature" label to new unlabeled issues |
| [f] 015 | 2025-03-06 | Add project velocity configuration settings |
| [f] 016 | 2025-03-06 | Add team strength to cycles |
| [f] 017 | 2025-03-07 | Implement velocity calculation and display |
| [f] 018 | 2025-03-11 | Add cycle creation events to Slack webhook notifications |

### Project Defaults

| Date | Description |
|------|-------------|
| 2025-01-21 | New projects have a set of customized PT-like states |
| 2025-02-05 | New projects have default Points estimate (1-6) |
| 2025-03-05 | New projects get default labels |

### Bug Fixes & Improvements

| Date | Description |
|------|-------------|
| 2025-01-16 | Support displaying arbitrary comment attachments |
| 2025-01-21 | Support uploading arbitrary attachment files to comments |
| 2025-02-03 | Fix: delete webhook for issues, issue_comments, projects |
| 2025-02-19 | Handle `Tab` key for selecting highlighted user in mention list |
| 2025-02-19 | Properly display initials in notification emails when user doesn't have avatar |
| 2025-02-21 | Customize slack payload for webhooks and filtering projects for each webhook |
| 2025-03-13 | Allow issue cycle update to select one latest past cycle as workaround |
| 2024-12-20 | Fix: issue serializer to remove deleted labels and assignees |

### Email Notifications

| Date | Description |
|------|-------------|
| 2025-02-18 | Ensure user can access notifications page without prior UserNotificationPreference record |
| 2025-02-18 | Tweak notification task to run more frequently (5min → 1 min) |

### Branding & UI

| Date | Description |
|------|-------------|
| 2025-03-24 | Remove some Plane brandings |
| 2025-03-24 | Update generic page title and description |
| 2026-02-06 | Add email to project invitee and make dropdown wider |

### Deployment & Infrastructure

| Date | Description |
|------|-------------|
| 2025-01-16 | Support dynamic GitHub repo for installing via environment variable |
| 2025-01-16 | Expose some ports for data import |
| 2025-01-16 | Always pull `live` image |
| 2025-02-04 | Add setup and migration guide for EA deployment |
| 2025-02-06 | Update EA's README |
| 2026-02-06 | Introduce K8s config files and README on how to deploy changes |

### Developer Tooling (Claude Code Setup — 2026-03-17)

| Date | Description |
|------|-------------|
| 2026-03-17 | Add `CLAUDE.md` with project conventions, tech stack, and key directories |
| 2026-03-17 | Add `.claude/settings.json` with permission rules |
| 2026-03-17 | Add `docs/` with architecture, frontend, backend, packages, dev, and deployment guides |
| 2026-03-17 | Add `.env.example` files for all 6 services with working local dev defaults |
| 2026-03-17 | Update development docs with accurate Docker setup instructions |

---

## Significant Upstream Changes Since Fork

The upstream `makeplane/plane` has made **1,749 commits** since our fork point, including several major structural changes that create divergence.

### Breaking / Structural Changes

| Change | Impact on our fork |
|--------|-------------------|
| **Vite migration** (`#7973`, `#7965`) — Next.js build replaced with Vite | Major — our fork still uses Next.js; merging will require build system migration |
| **Directory restructure** — `apiserver/` → `apps/api/` | Major — all our backend customizations reference the old path |
| **ESLint → OxLint** (`#8677`) and **Prettier → oxfmt** (`#8676`) | Moderate — our linting setup would need to change |
| **"Issues" renamed to "Work Items"** throughout the UI | Moderate — terminology changes across components |
| **Navigation restructure** (`#8156`) | Moderate — UI navigation rewritten |
| **pytest test framework** with unit/contract/smoke categories | Minor positive — better test infrastructure we can adopt |
| **Django version upgrades** | Minor — dependency updates |

### New Upstream Features (not in our fork)

| Feature | PR/Ref |
|---------|--------|
| Wiki / Pages v2 with collaborative editing enhancements | WIKI-* series |
| Work item comments redesign | WEB-5312 |
| Getting started checklist and tips for workspaces | WEB-5890 |
| Project summary external API | SILO-1028 |
| Enhanced authentication logging | WEB-5225 |
| Webhook versioning and rate limiting | Multiple |
| SSRF security fixes for webhooks and work item links | SECUR-113, SECUR-116 |
| IDOR vulnerability fixes for assets & attachments | #8644 |
| Member information disclosure fix | #8646 |

### Upstream Security Fixes (should consider backporting)

| Fix | PR |
|-----|-----|
| SSRF webhook URL for IP address | #8716 |
| SSRF for work item links | #8607 |
| IDOR vulnerabilities in asset & attachment endpoints | #8644 |
| Member information disclosure via public endpoint | #8646 |

---

## Merge Strategy Considerations

Due to the scale of upstream changes (7,807 files, directory restructure, Vite migration), a direct merge is not practical. Options:

1. **Cherry-pick security fixes** — Backport the 4 security fixes listed above to our fork immediately.
2. **Rebase on upstream** — Re-apply our 40 commits on top of the latest upstream. High effort due to structural changes (`apiserver/` → `apps/api/`, Next.js → Vite).
3. **Feature-port to upstream** — Start from fresh upstream and re-implement our EA customizations. Most sustainable long-term approach.
4. **Stay on current fork** — Continue with our version, only cherry-picking critical fixes. Lowest effort but increases divergence over time.
