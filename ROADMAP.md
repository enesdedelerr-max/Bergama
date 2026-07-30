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
Release tag `v0.4.0-sprint4` exists.

See [`docs/sprints/sprint-4/README.md`](docs/sprints/sprint-4/README.md).

### Sprint 5 — Strategy SDK Hardening

Status: complete. Issue **#51** merged through PR **#52**.
Implementation baseline: `260ffbecb4113040705dc44a768ebf6e75f933ea`.
Release tag `v0.5.0-sprint5` is prepared but has **not** been created.

See [`docs/sprints/sprint-5/README.md`](docs/sprints/sprint-5/README.md).

### Sprint 6 — Feature Platform

Status: complete. Planning issue **#65**; implementation issues **#66–#68**
merged through PR **#69**.
Implementation baseline: `a04b9e5d5b5673a3f4f2022159915b520995bf06`.
Release tag `v0.6.0-sprint6` is prepared but has **not** been created.

See [`docs/sprints/sprint-6/README.md`](docs/sprints/sprint-6/README.md).

### Sprint 7 — Premarket Intelligence

Status: complete. Planning issue **#71**; implementation issues **#72**,
**#74**, and **#76** merged through PRs **#73**, **#75**, and **#77**.
Implementation baseline: `3b8358e728555bc17da87786b3a2f41792559433`.
Release tag `v0.7.0-sprint7`.

See [`docs/sprints/sprint-7/README.md`](docs/sprints/sprint-7/README.md).

### Next action

1. Sprint 7 governance closeout and release tag `v0.7.0-sprint7` are complete.
2. Next sprint planning remains pending and is not authorized by Sprint 7
   closeout.

## Sprint sequence

1. Sprint 0 — Repository and Toolchain — Complete
2. Sprint 1 — Infrastructure — Complete
3. Sprint 2 — FastAPI Runtime — Complete
4. Sprint 3 — Market Data Plane — Complete
5. Sprint 4 — Trading Foundations — Complete
6. Sprint 5 — Strategy SDK Hardening — Complete
7. Sprint 6 — Feature Platform — Complete
8. Sprint 7 — Premarket Intelligence — Complete
9. Sprint 8 — AI Decision Engine — Planned
10. Sprint 9 — Dashboard — Planned
11. Sprint 10 — MLOps — Planned
12. Sprint 11 — Research — Planned
13. Sprint 12 — Compliance — Planned
14. Sprint 13 — Production Hardening — Planned
15. Sprint 14 — Live Pilot — Planned
16. Sprint 15 — Limited Production Stabilization — Planned

### Notes on later themes

Sprint 4 already delivered foundational Broker, Portfolio, Risk, OMS, and
Strategy Engine / Strategy SDK runtime slices. Later sprints named historically
as “Broker and Execution” or “Portfolio Runtime” should be treated as
**deepening / productionization** of those foundations, not greenfield
reintroduction of the same bounded contexts.

## Planning principles

- Complete dependencies before dependent work.
- Prefer vertical slices.
- Avoid broad rewrites.
- Keep each issue independently mergeable.
- Do not start the next sprint before the current exit gate passes.
- Reliability, security and auditability are release blockers.
- Live execution is never enabled by default.
