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

### Sprint 8 — Premarket Scoring Foundation

Status: complete. Issue **#78** merged through PR **#79**.
Implementation baseline: `dedccab35d3238f6cc9840689ca61a99cc454ce6`.
Release tag `v0.8.0-sprint8`.

See [`docs/sprints/sprint-8/README.md`](docs/sprints/sprint-8/README.md).

### Sprint 9 — Morning Briefing Foundation

Status: complete. Issue **#82** merged through PR **#83**.
Implementation baseline: `a713bea13b352f35a9390f68ce43081b68587eb9`.
Release tag `v0.9.0-sprint9` exists. GitHub Release is published. Milestone
is closed.

See [`docs/sprints/sprint-9/README.md`](docs/sprints/sprint-9/README.md).

### Sprint 10 — Dashboard Foundation

Status: complete. Issue **#85** merged through PR **#86**.
Implementation baseline: `c87b1afdca60f0eb4c734c75ed1aeba71de69646`.
Closeout merge: `1ed9e86deed12088399e5b74b648c664de4dc123`.
Release tag `v0.10.0-sprint10` is **RELEASED**. GitHub Release is **PUBLISHED**.
Sprint 10 milestone is **CLOSED**.

See [`docs/sprints/sprint-10/README.md`](docs/sprints/sprint-10/README.md).

### Sprint 11 — Human Review Foundation

Status: complete. Issue **#89** merged through PR **#90**.
Implementation baseline: `baf1ae03312418cfe6a17d8615ccfec62d14f8c0`.
Closeout merge: `201999b101a745d64d479fda8303b5dc5bd74d9a`.
Release tag `v0.11.0-sprint11` is **RELEASED**. GitHub Release is **PUBLISHED**.
Sprint 11 milestone is **CLOSED**.

See [`docs/sprints/sprint-11/README.md`](docs/sprints/sprint-11/README.md).

### Next action

Next repository work requires a new Planning Gate.

## Sprint sequence

1. Sprint 0 — Repository and Toolchain — Complete
2. Sprint 1 — Infrastructure — Complete
3. Sprint 2 — FastAPI Runtime — Complete
4. Sprint 3 — Market Data Plane — Complete
5. Sprint 4 — Trading Foundations — Complete
6. Sprint 5 — Strategy SDK Hardening — Complete
7. Sprint 6 — Feature Platform — Complete
8. Sprint 7 — Premarket Intelligence — Complete
9. Sprint 8 — Premarket Scoring Foundation — Complete
10. Sprint 9 — Morning Briefing Foundation — Complete
11. Sprint 10 — Dashboard Foundation — Complete
12. Sprint 11 — Human Review Foundation — Complete

### Downstream sequencing (future Planning Gates required)

```text
Sprint 8 Premarket Scoring
  → Sprint 9 Morning Briefing
  → Sprint 10 Dashboard Foundation (complete)
  → Sprint 11 Human Review Foundation (complete)
  → AI Decision Engine (future; not authorized)
  → Broker Execution (future; not authorized)
```

Human Review Foundation is implemented. AI Decision Engine and Broker Execution
remain deferred future work. They are **not** authorized by Sprint 11 closeout.
No sprint number is assigned to them. Next implementation work requires a new
approved Planning Gate.

### Notes on later themes

Sprint 4 already delivered foundational Broker, Portfolio, Risk, OMS, and
Strategy Engine / Strategy SDK runtime slices. Later work named historically
as “Broker and Execution” or “Portfolio Runtime” should be treated as
**deepening / productionization** of those foundations, not greenfield
reintroduction of the same bounded contexts.

Earlier roadmap drafts listed Sprint 8 as “AI Decision Engine”. Sprint 8
delivered **Premarket Scoring Foundation** instead. AI Decision Engine remains
deferred future work and was not delivered by Sprint 8.

Earlier roadmap drafts listed Sprint 9 as “Dashboard”. Sprint 9 delivered
**Morning Briefing Foundation** instead. Dashboard Foundation was delivered by
Sprint 10. Human Review Foundation was delivered by Sprint 11. AI Decision
Engine and Broker Execution remain unauthorized until a new Planning Gate.

## Planning principles

- Complete dependencies before dependent work.
- Prefer vertical slices.
- Avoid broad rewrites.
- Keep each issue independently mergeable.
- Do not start the next sprint before the current exit gate passes.
- Reliability, security and auditability are release blockers.
- Live execution is never enabled by default.
