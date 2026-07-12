# AI Hedge Fund Operating System

An institutional-grade, AI-native trading platform built around deterministic
data processing, policy-controlled decisions, safe execution, complete
portfolio accounting and production operational governance.

## Current status

The repository is in implementation mode.

Current focus:

```text
Sprint 1 — Infrastructure Finalization
```

Sprint 2 is blocked until:

```bash
make gate-sprint1
```

passes completely.

## Core principles

- Deterministic and replayable
- Point-in-time safe
- Strongly typed
- Secure by default
- Idempotent execution
- Append-only audit and ledger
- Human and policy approval gates
- Observable failure modes
- Reproducible builds
- Safe rollback and recovery

## Engineering workflow

Before changing the repository:

1. Read `AGENTS.md`.
2. Read `PROJECT.md`.
3. Read `ARCHITECTURE.md`.
4. Read relevant `.cursor/rules/*.mdc`.
5. Inspect the existing implementation.
6. Work on one issue only.
7. Run required quality gates.
8. Report exact executed validation.

## High-level stack

- Python 3.13 / FastAPI
- Next.js / React / TypeScript
- PostgreSQL / Redis / Kafka / ClickHouse
- MinIO / Apache Iceberg
- Kubernetes / Helm / ArgoCD
- Prometheus / Grafana / Loki / Tempo

## Applications

- [`apps/platform-console`](apps/platform-console) — read-only Platform Operations Console shell (typed mock health contracts)

## Safety statement

This system may eventually interact with real financial accounts.

No component should be considered production-safe until its relevant:

- tests,
- reconciliation,
- security,
- risk,
- compliance,
- operational readiness,
- live-pilot gates

have all passed.
