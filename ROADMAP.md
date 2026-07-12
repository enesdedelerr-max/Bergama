# ROADMAP.md

## Delivery model

The project is delivered sprint by sprint.

Every sprint must produce:

- working code,
- automated tests,
- updated operational documentation,
- deployable artifacts,
- sprint summary,
- risks,
- rollback notes.

## Current status

### Sprint 0 — Repository and developer platform

Status: implementation baseline established.

### Sprint 1 — Infrastructure foundation

Status: finalization gate in progress.

Required exit command:

```bash
make gate-sprint1
```

Sprint 2 is blocked until the Sprint 1 gate passes.

## Sprint sequence

1. Sprint 0 — Repository and Toolchain
2. Sprint 1 — Infrastructure
3. Sprint 2 — FastAPI Runtime
4. Sprint 3 — Market Data Plane
5. Sprint 4 — Feature Platform
6. Sprint 5 — Premarket Intelligence
7. Sprint 6 — AI Decision Engine
8. Sprint 7 — Broker and Execution
9. Sprint 8 — Portfolio Runtime
10. Sprint 9 — Dashboard
11. Sprint 10 — MLOps
12. Sprint 11 — Research
13. Sprint 12 — Compliance
14. Sprint 13 — Production Hardening
15. Sprint 14 — Live Pilot
16. Sprint 15 — Limited Production Stabilization

## Planning principles

- Complete dependencies before dependent work.
- Prefer vertical slices.
- Avoid broad rewrites.
- Keep each issue independently mergeable.
- Do not start the next sprint before the current exit gate passes.
- Reliability, security and auditability are release blockers.
- Live execution is never enabled by default.
