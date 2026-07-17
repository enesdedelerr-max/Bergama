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

Status: complete.

### Sprint 1 — Infrastructure foundation

Status: complete. Tag `v0.1.0-sprint1`. Gate: `make gate-sprint1` PASS.

### Sprint 2 — FastAPI runtime

Status: complete. Tag `v0.2.0-sprint2`. Gate: `make gate-sprint2` PASS (GO FOR SPRINT 3).

See [`docs/sprints/sprint-2/README.md`](docs/sprints/sprint-2/README.md).

### Sprint 3 — Market Data Plane

Status: complete. Tag `v0.3.0-sprint3`. Gate: `make gate-sprint3` PASS.

See [`docs/sprints/sprint-3/README.md`](docs/sprints/sprint-3/README.md).

### Sprint 4 — Trading Foundations

Status: complete. Issues **#401–#406** merged through PRs **#44–#49**.
Implementation baseline: `199f8a04a87842ea4d44ea182ed45f5a28d4466a`.
Release tag `v0.4.0-sprint4` is prepared but has not been created.

See [`docs/sprints/sprint-4/README.md`](docs/sprints/sprint-4/README.md).

### Next sprint

Next sprint planning pending.

## Sprint sequence

1. Sprint 0 — Repository and Toolchain
2. Sprint 1 — Infrastructure
3. Sprint 2 — FastAPI Runtime
4. Sprint 3 — Market Data Plane
5. Sprint 4 — Trading Foundations
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
