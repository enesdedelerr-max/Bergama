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

Status: **COMPLETE**. Planning APPROVED. Architecture APPROVED. Governance
Decisions #1–#8 RESOLVED. Governance COMPLETE — documentation-only. Policy
Version `ai-decision-engine.policy.v1` APPROVED. Implementation Authorization
`ai-decision-engine.implementation-authorization.v1` APPROVED. ADE Foundation
implementation COMPLETE (Issue #110 CLOSED; PR #111 MERGED @
`51b3afffb5804f2de307c8b4e582447e92b77c9d`). Implementation-status
synchronization COMPLETE (Issue #112 CLOSED; PR #113 MERGED @
`f1dfd0853a49b49c5b2b75dc6c5a96230ef23a19`). Governance closeout COMPLETE
under Issue #114
([`docs/sprints/sprint-12/CLOSEOUT.md`](docs/sprints/sprint-12/CLOSEOUT.md)).

`SPRINT_COMPLETE ≠ CAPABILITY_AUTHORIZATION`

MODEL PARTICIPATION remains UNAUTHORIZED. Broker Execution remains
DENIED / DEFERRED. Human Disposition remains
`OPTIONAL — NOT IMPLEMENTED — NOT REQUIRED FOR CLOSEOUT`. Tag / release remain
unauthorized and not performed.

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
| Implementation | FOUNDATION COMPLETE — Issue #110 CLOSED; PR #111 MERGED @ `51b3afffb5804f2de307c8b4e582447e92b77c9d` |
| Status sync | COMPLETE — Issue #112 CLOSED; PR #113 MERGED @ `f1dfd0853a49b49c5b2b75dc6c5a96230ef23a19` |
| Closeout | COMPLETE — Issue #114 |
| Human Disposition | OPTIONAL — NOT IMPLEMENTED — NOT REQUIRED FOR CLOSEOUT |
| Broker Execution | DENIED / DEFERRED |
| MODEL PARTICIPATION | UNAUTHORIZED |
| Tag / release | NOT AUTHORIZED / NOT PERFORMED |

Architecture approval does **not** authorize unbounded AI Decision Engine
implementation. Governance Decisions #1–#8 are RESOLVED. Governance is COMPLETE
for the planned decision set. Policy Version `ai-decision-engine.policy.v1` is
APPROVED. Implementation Authorization is APPROVED. ADE Foundation
implementation is COMPLETE strictly within
`ai-decision-engine.implementation-authorization.v1`. Sprint 12 governance
closeout is COMPLETE under Issue #114. MODEL PARTICIPATION remains
UNAUTHORIZED.

See [`docs/sprints/sprint-12/README.md`](docs/sprints/sprint-12/README.md) and
[`docs/sprints/sprint-12/CLOSEOUT.md`](docs/sprints/sprint-12/CLOSEOUT.md).

### Sprint 13 — Intelligence Pipeline Integration

Status: **COMPLETE**. Planning Gate `sprint-13.planning-gate` APPROVED /
EFFECTIVE. Architecture `intelligence-pipeline.architecture.v1` APPROVED /
EFFECTIVE. Governance `intelligence-pipeline.governance.v1` APPROVED /
EFFECTIVE. Policy Version `intelligence-pipeline.policy.v1` APPROVED / FROZEN.
Implementation Authorization
`intelligence-pipeline.implementation-authorization.v1` APPROVED / EFFECTIVE.
Implementation sequence 3/3 COMPLETE:

- Issue **#126** / PR **#127** — Core admission and orchestration through Dashboard
- Issue **#128** / PR **#129** — Optional Human Review and ADE terminals
- Issue **#130** / PR **#131** — Replay, determinism, and authority-firewall hardening

Authoritative implementation baseline:
`195c1c9eae1a8b3258b04e9a37dca562a051a371`. Implementation-status
synchronization COMPLETE (Issue **#132** CLOSED; PR **#133** MERGED @
`810be70e80acfe6f172910faf15505832eece3aa`; post-merge quality gate
`37398770759` completed / success). Governance closeout COMPLETE under
Issue **#134**
([`docs/sprints/sprint-13/CLOSEOUT.md`](docs/sprints/sprint-13/CLOSEOUT.md)).

```text
IMPLEMENTATION_COMPLETE = YES
GOVERNANCE_CLOSEOUT = COMPLETE
SPRINT_COMPLETE = YES
SPRINT_COMPLETE ≠ CAPABILITY_AUTHORIZATION
TAG_RELEASE_AUTHORIZED = NO
```

MODEL PARTICIPATION remains UNAUTHORIZED. Broker Execution remains
DENIED / DEFERRED. Tag / release / deployment remain unauthorized. Sprint 14
subsequently proceeded under its own Planning → Architecture → Governance →
Policy → Implementation Authorization chain (see Sprint 14 below).

Theme: Intelligence Pipeline Integration.
Planning Gate ID: `sprint-13.planning-gate`.
Architecture ID: `intelligence-pipeline.architecture.v1`.
Governance ID: `intelligence-pipeline.governance.v1`.
Policy Version ID: `intelligence-pipeline.policy.v1`.
Implementation Authorization ID: `intelligence-pipeline.implementation-authorization.v1`.

| Field | Value |
| --- | --- |
| Planning | APPROVED / EFFECTIVE |
| Architecture | APPROVED / EFFECTIVE |
| Governance | APPROVED / EFFECTIVE |
| Policy Freeze | APPROVED / FROZEN |
| Implementation Authorization | APPROVED / EFFECTIVE |
| Implementation | 3/3 COMPLETE — #126 / #128 / #130 |
| Status sync | COMPLETE — Issue #132 / PR #133 |
| Closeout | COMPLETE — Issue #134 |
| Broker Execution | DENIED / DEFERRED |
| MODEL PARTICIPATION | UNAUTHORIZED |
| Tag / release | NOT AUTHORIZED / NOT PERFORMED |

See [`docs/sprints/sprint-13/README.md`](docs/sprints/sprint-13/README.md) and
[`docs/sprints/sprint-13/CLOSEOUT.md`](docs/sprints/sprint-13/CLOSEOUT.md).

### Sprint 14 — Durable Intelligence Run Persistence and Read/Query Boundary

Status: **COMPLETE** (documentation target). Planning Gate
`sprint-14.planning-gate` APPROVED / EFFECTIVE. Architecture
`intelligence-run-productization.architecture.v1` APPROVED / EFFECTIVE.
Governance `intelligence-run-productization.governance.v1` APPROVED /
EFFECTIVE. Policy Version `intelligence-run-productization.policy.v1` APPROVED
/ FROZEN. Implementation Authorization
`intelligence-run-productization.implementation-authorization.v1` APPROVED /
EFFECTIVE. Implementation workstreams 4/4 COMPLETE:

- Issue **#146** / PR **#147** — Persistence schema / repository / migrations
- Issue **#148** / PR **#149** — Materializer / snapshot contract
- Issue **#150** / PR **#151** — Query service / read API
- Issue **#152** / PR **#153** — Productization hardening / authorization firewalls

Authoritative implementation baseline:
`748bc9977a8910565c05705b7467da71c4162de5`. Post-merge quality gate
`37724824835` completed / success. Implementation-status synchronization is
COMPLETE (Issue **#154** CLOSED; PR **#155** MERGED @
`d72282b555bcd17b89e8e51ef145a70ca7eb4bca`; post-merge CI `37729140437`
success). Governance closeout is recorded under Issue **#156**
([`docs/sprints/sprint-14/CLOSEOUT.md`](docs/sprints/sprint-14/CLOSEOUT.md)).

```text
IMPLEMENTATION_COMPLETE = YES
STATUS_SYNC = COMPLETE
GOVERNANCE_CLOSEOUT = COMPLETE
SPRINT_COMPLETE = YES
SPRINT_COMPLETE ≠ CAPABILITY_AUTHORIZATION
SPRINT_15_IMPLEMENTATION_AUTHORIZED = NO
```

Lifecycle note: documentation target is COMPLETE; operational Sprint 14
completion is recognized only after Closeout PR merge, post-merge main CI
green, and Issue #156 closure.

MODEL PARTICIPATION remains UNAUTHORIZED. Broker Execution remains
DENIED / DEFERRED. Public write API remains UNAUTHORIZED / NOT IMPLEMENTED. UI
implementation, Feature Platform expansion, live-provider expansion, tag,
release, and deployment remain unauthorized. Sprint 15 implementation remains
unauthorized; only a separate Sprint 15 planning/discovery gate may follow.

Theme: Durable Intelligence Run Persistence and Read/Query Boundary.
Planning Gate ID: `sprint-14.planning-gate`.
Architecture ID: `intelligence-run-productization.architecture.v1`.
Governance ID: `intelligence-run-productization.governance.v1`.
Policy Version ID: `intelligence-run-productization.policy.v1`.
Implementation Authorization ID: `intelligence-run-productization.implementation-authorization.v1`.

| Field | Value |
| --- | --- |
| Planning | APPROVED / EFFECTIVE |
| Architecture | APPROVED / EFFECTIVE |
| Governance | APPROVED / EFFECTIVE |
| Policy Freeze | APPROVED / FROZEN |
| Implementation Authorization | APPROVED / EFFECTIVE |
| Implementation | 4/4 COMPLETE — #146 / #148 / #150 / #152 |
| Status sync | COMPLETE — Issue #154 / PR #155 |
| Closeout | COMPLETE — Issue #156 |
| Broker Execution | DENIED / DEFERRED |
| MODEL PARTICIPATION | UNAUTHORIZED |
| Tag / release | NOT AUTHORIZED / NOT PERFORMED |
| Sprint 15 implementation | NOT AUTHORIZED |

See [`docs/sprints/sprint-14/README.md`](docs/sprints/sprint-14/README.md) and
[`docs/sprints/sprint-14/CLOSEOUT.md`](docs/sprints/sprint-14/CLOSEOUT.md).

### Next action

Perform a separate Sprint 15 planning/discovery gate for a read-only
Premarket Command Center / ADE visibility UI when ready. Do **not** start
Sprint 15 / UI implementation, model participation, broker execution, tag,
release, or deployment from Sprint 14 Closeout. Broker Execution remains
DENIED / DEFERRED. MODEL PARTICIPATION remains UNAUTHORIZED.
`SPRINT_15_IMPLEMENTATION_AUTHORIZED = NO`.

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
13. Sprint 12 — AI Decision Engine Foundation — Complete
14. Sprint 13 — Intelligence Pipeline Integration — Complete
15. Sprint 14 — Durable Intelligence Persistence — Complete

### Downstream sequencing

```text
Sprint 8  Premarket Scoring       COMPLETE / RELEASED
  → Sprint 9  Morning Briefing        COMPLETE / RELEASED
  → Sprint 10 Dashboard               COMPLETE / RELEASED
  → Sprint 11 Human Review            COMPLETE / RELEASED
  → Sprint 12 AI Decision Engine      COMPLETE
  → Sprint 13 Intelligence Pipeline   COMPLETE
  → Sprint 14 Intelligence Persistence COMPLETE
  → Sprint 15 Premarket / ADE UI planning   future / planning only
  → Broker Execution                       future / unauthorized
```

Sprint 12 is COMPLETE under Issue #114. Sprint 13 is COMPLETE under Issue #134
(authorized implementation Issues #126 / #128 / #130; status sync Issue #132 /
PR #133; governance closeout Issue #134). Sprint 14 authorized implementation
is COMPLETE (Issues #146 / #148 / #150 / #152). Status sync is COMPLETE
(Issue #154 / PR #155). Sprint 14 governance closeout is recorded under
Issue #156. Sprint 15 implementation remains unauthorized. Broker Execution
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
Authorization is APPROVED. ADE Foundation implementation is COMPLETE within
approved bounded scope. Sprint 12 governance closeout is COMPLETE under
Issue #114. Broker Execution remains unauthorized.

## Planning principles

- Complete dependencies before dependent work.
- Prefer vertical slices.
- Avoid broad rewrites.
- Keep each issue independently mergeable.
- Do not start the next sprint before the current exit gate passes.
- Reliability, security and auditability are release blockers.
- Live execution is never enabled by default.
