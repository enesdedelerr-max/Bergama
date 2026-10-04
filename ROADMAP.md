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

### Sprint 12 — AI Decision Engine Foundation

Status: Planning APPROVED. Architecture APPROVED. Governance Decisions #1–#8
RESOLVED. Governance COMPLETE — documentation-only. Policy Version
`ai-decision-engine.policy.v1` APPROVED. Implementation Authorization
`ai-decision-engine.implementation-authorization.v1` APPROVED. Implementation
is AUTHORIZED within the approved bounded scope. Sprint 12 is **not**
complete. MODEL PARTICIPATION remains UNAUTHORIZED.

Theme: AI Decision Engine Foundation.
Planning Gate ID: `sprint-12.planning-gate`.
Architecture ID: `ai-decision-engine.architecture.v1`.
Governance Decision #1 ID: `ai-decision-engine.governance.01-semantic-boundary`.
Governance Decision #2 ID: `ai-decision-engine.governance.02-authorized-inputs`.
Governance Decision #3 ID: `ai-decision-engine.governance.03-ai-decision-authority`.
Governance Decision #4 ID: `ai-decision-engine.governance.04-identity`.
Governance Decision #5 ID: `ai-decision-engine.governance.05-provenance`.
Governance Decision #6 ID: `ai-decision-engine.governance.06-replay-pit`.
Governance Decision #7 ID: `ai-decision-engine.governance.07-output-abstention`.
Governance Decision #8 ID: `ai-decision-engine.governance.08-human-authority`.
Policy Version ID: `ai-decision-engine.policy.v1`.
Implementation Authorization ID: `ai-decision-engine.implementation-authorization.v1`.

| Field | Value |
| --- | --- |
| Planning | APPROVED |
| Architecture | APPROVED |
| Architecture approved | Yes |
| Governance | COMPLETE — documentation-only |
| Governance Decision #1 | RESOLVED |
| Governance Decision #2 | RESOLVED |
| Governance Decision #3 | RESOLVED |
| Governance Decision #4 | RESOLVED |
| Governance Decision #5 | RESOLVED |
| Governance Decision #6 | RESOLVED |
| Governance Decision #7 | RESOLVED |
| Governance Decision #8 | RESOLVED |
| Policy Freeze | APPROVED |
| Implementation Authorization | APPROVED |
| Implementation | AUTHORIZED — bounded by approved Implementation Authorization |
| Broker Execution | DENIED / DEFERRED |

Architecture approval does **not** authorize unbounded AI Decision Engine
implementation. Governance Decisions #1–#8 are RESOLVED. Governance is COMPLETE
for the planned decision set. Policy Version `ai-decision-engine.policy.v1` is
APPROVED. Implementation Authorization is APPROVED. Implementation is AUTHORIZED
strictly within `ai-decision-engine.implementation-authorization.v1`. MODEL
PARTICIPATION remains UNAUTHORIZED.

See [`docs/sprints/sprint-12/README.md`](docs/sprints/sprint-12/README.md).

### Next action

Create the first separately numbered ADE foundation implementation issue(s)
within Approved Scope under approved Implementation Authorization
(`ai-decision-engine.implementation-authorization.v1`).

Implementation Authorization approval does not complete Sprint 12 and does not
authorize model participation, Broker Execution, trading authority, Order
Intent, or OMS. Broker Execution remains DENIED / DEFERRED. MODEL PARTICIPATION
remains UNAUTHORIZED.

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
13. Sprint 12 — AI Decision Engine Foundation — Planning APPROVED

### Downstream sequencing

```text
Sprint 8  Premarket Scoring       COMPLETE / RELEASED
  → Sprint 9  Morning Briefing        COMPLETE / RELEASED
  → Sprint 10 Dashboard               COMPLETE / RELEASED
  → Sprint 11 Human Review            COMPLETE / RELEASED
  → Sprint 12 AI Decision Engine      IMPL AUTH APPROVED
  → Broker Execution                  future / unauthorized
```

Human Review Foundation is implemented. Sprint 12 Planning is APPROVED.
Implementation Authorization is APPROVED. AI Decision Engine implementation is
AUTHORIZED within approved bounded scope and has not started. Broker Execution
remains deferred future work and is **not** authorized.

### Notes on later themes

Sprint 4 already delivered foundational Broker, Portfolio, Risk, OMS, and
Strategy Engine / Strategy SDK runtime slices. Later work named historically
as “Broker and Execution” or “Portfolio Runtime” should be treated as
**deepening / productionization** of those foundations, not greenfield
reintroduction of the same bounded contexts.

Earlier roadmap drafts listed Sprint 8 as “AI Decision Engine”. Sprint 8
delivered **Premarket Scoring Foundation** instead. AI Decision Engine was
not delivered by Sprint 8.

Earlier roadmap drafts listed Sprint 9 as “Dashboard”. Sprint 9 delivered
**Morning Briefing Foundation** instead. Dashboard Foundation was delivered by
Sprint 10. Human Review Foundation was delivered by Sprint 11. Sprint 12
Planning for AI Decision Engine Foundation is APPROVED. Implementation
Authorization is APPROVED. Implementation is AUTHORIZED within approved bounded
scope. Broker Execution remains unauthorized.

## Planning principles

- Complete dependencies before dependent work.
- Prefer vertical slices.
- Avoid broad rewrites.
- Keep each issue independently mergeable.
- Do not start the next sprint before the current exit gate passes.
- Reliability, security and auditability are release blockers.
- Live execution is never enabled by default.
