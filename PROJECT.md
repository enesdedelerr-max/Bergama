# PROJECT.md

## Project name

AI Hedge Fund Operating System

## Vision

Build a production-grade institutional trading platform that combines:

- canonical market data,
- point-in-time-safe features,
- premarket intelligence,
- AI-assisted decisions,
- controlled execution,
- portfolio accounting,
- risk management,
- compliance,
- research,
- MLOps,
- operational governance.

The platform must be safe enough to progress from:

```text
local simulation
→ replay
→ paper trading
→ broker sandbox
→ limited-capital pilot
→ controlled production
```

## Product goals

- Deterministic and replayable workflows
- Reliable market-data processing
- Point-in-time-safe research and features
- Explainable trading decisions
- Strict human and policy approval gates
- Idempotent execution
- Complete order/fill reconciliation
- Double-entry portfolio accounting
- Observable risk and operational state
- Secure, reproducible deployments
- Evidence-backed production releases

## Current phase

Execution mode.

The current work should follow the sprint backlog.

Do not add broad speculative features.

Sprint 1 infrastructure finalization is complete (`v0.1.0-sprint1`).

The immediate objective is Sprint 2 — FastAPI runtime foundation, starting with
Issue **#201 FastAPI Runtime Bootstrap** on branch `feature/sprint2-runtime`.

## Current sprint

Sprint 2 issue chain: #201 → #202 → … → #210 → Sprint 2 Gate.

Package root: `apps/api`.

## Primary stack

### Backend

- Python 3.13
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query
- TanStack Table
- Playwright

### Data and messaging

- PostgreSQL
- pgvector
- TimescaleDB
- Redis
- Kafka
- ClickHouse
- MinIO
- Apache Iceberg

### Infrastructure

- Docker
- Docker Compose
- Kind
- Kubernetes
- Helm
- ArgoCD

### Observability

- OpenTelemetry
- Prometheus
- Grafana
- Loki
- Tempo

## Non-goals

- Hidden shortcuts
- Fake provider integrations
- Unapproved live execution
- Architecture rewrites during small issues
- Speculative abstractions
- Unpinned dependencies
- Mutable audit or accounting history
- UI-only enforcement of security or financial controls
- Production claims without runtime evidence

## Engineering success criteria

A change is valuable only when it produces:

- working code,
- automated tests,
- clear contracts,
- observable behavior,
- deployable artifacts,
- reproducible validation,
- documented limitations.
