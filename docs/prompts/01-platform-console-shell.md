# Platform Operations Console shell — task prompt

Use this as a separate issue prompt. Do not implement the full Sprint 9 dashboard early.
Build only the initial read-only Developer/Operations Console shell.

---

Task: Build the initial read-only Platform Operations Console shell.

First read:

- `AGENTS.md`
- `PROJECT.md`
- `ARCHITECTURE.md`
- `ROADMAP.md`
- relevant Cursor rules
- existing frontend code

## Scope

Create a production-quality frontend shell that will later surface
infrastructure and runtime health.

This task must include only:

- authenticated-layout scaffold or local bootstrap session scaffold,
- responsive application shell,
- navigation,
- overview page,
- typed mock contract layer,
- loading, empty and error states,
- light/dark theme support,
- accessibility baseline.

## Navigation

- Overview
- Infrastructure
- Data Services
- GitOps
- Releases
- Logs
- Metrics
- Settings

## Overview cards

- Kubernetes
- ArgoCD
- PostgreSQL
- Redis
- Kafka
- ClickHouse
- MinIO
- Iceberg
- Prometheus
- Grafana
- Loki
- Tempo
- Sprint 1 Gate

Each service card must support:

- healthy
- degraded
- unavailable
- unknown
- stale

Display:

- status
- environment
- version
- last checked time
- short message

## Technical stack

- Next.js App Router
- React
- TypeScript strict
- Tailwind CSS
- shadcn/ui
- TanStack Query
- TanStack Table where appropriate

## Architecture

- components must not contain business logic,
- API access must live in `lib/api`,
- query hooks must live in hooks or feature-level query modules,
- response types must live in contracts/types,
- server state must use TanStack Query,
- local UI state must remain local.

## Out of scope

- real trading screens,
- broker execution actions,
- order placement,
- live kill-switch controls,
- production OIDC,
- backend service implementation,
- billing,
- tenant administration,
- complex charts.

## Required states

- loading
- empty
- partial
- stale
- error
- unauthorized

## Testing

- unit tests for status mapping,
- integration test for dashboard rendering,
- error and empty-state tests,
- responsive Playwright smoke test if Playwright is already configured.

## Before coding

1. Inspect the current frontend.
2. List files to create or modify.
3. Identify existing design system conventions.
4. Confirm no unrelated refactor is required.

## After implementation run

- frontend format check
- lint
- TypeScript typecheck
- unit/integration tests
- production build
- Playwright smoke test if available

Do not claim any command passed unless it ran successfully.

Do not implement future dashboard modules.
