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

The immediate objective is to complete Sprint 1 infrastructure finalization,
pass `make gate-sprint1`, and only then begin Sprint 2.

## Current sprint gate

Sprint 1 is complete only when:

- infrastructure health is 100%,
- GitOps is Healthy and Synced,
- Helm lint and rendering pass,
- stateful services are healthy,
- backup and restore smoke pass,
- version locks pass,
- secrets validation passes,
- platform validation passes,
- release artifacts, checksums and SBOM exist,
- no default credentials remain,
- Git tag `v0.1.0-sprint1` exists.

Required command:

```bash
make gate-sprint1
```

Sprint 2 must not start unless this command succeeds.

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
