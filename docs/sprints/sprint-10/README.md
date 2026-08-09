# Sprint 10 — Dashboard Foundation

## Status

COMPLETE.

Sprint 10 theme is **Dashboard Foundation**. Authorized implementation scope
is Issue **#85**, merged on `main` through PR **#86**. The implementation
baseline / rollback reference is:

```text
c87b1afdca60f0eb4c734c75ed1aeba71de69646
```

| Field | Value |
| --- | --- |
| Sprint | Sprint 10 |
| Theme | Dashboard Foundation |
| Status | COMPLETE |
| Implementation Issue | [#85](https://github.com/enesdedelerr-max/Bergama/issues/85) — CLOSED / COMPLETED |
| Implementation PR | [#86](https://github.com/enesdedelerr-max/Bergama/pull/86) — MERGED |
| Implementation baseline | `c87b1afdca60f0eb4c734c75ed1aeba71de69646` |
| Feature branch | `feature/sprint10-85-dashboard-foundation` — deleted |
| Milestone | Sprint 10 — still **OPEN** pending closeout completion |
| Release tag | `v0.10.0-sprint10` — PREPARED / **NOT CREATED** |
| GitHub Release | **NOT PUBLISHED** |

Human Review, AI Decision Engine, Broker Execution, UI, HTTP APIs,
persistence, workers, schedulers, and notifications remain deferred or out of
scope per Issue **#85** and are not part of the executed Sprint 10
implementation scope.

Sprint 10 Planning Gate, Dashboard Architecture v1, Governance Decisions
#1–#8, Policy Version `dashboard.policy.v1`, and Implementation Authorization
v1 are repository-backed under `docs/sprints/sprint-10/`,
`docs/architecture/`, `docs/governance/dashboard/`, and `docs/policy/`. They
were merged with PR #86 and are immutable relative to this closeout.

Governance closeout is recorded in [`CLOSEOUT.md`](CLOSEOUT.md). Release tag
creation for Sprint 10 remains a separate maintainer action after this closeout
is merged. Preferred tag target is the closeout merge tip on `main`, not the
implementation baseline.

## Objective

Introduce the Dashboard bounded context under Policy Version
`dashboard.policy.v1` as a deterministic, read-only, presentation-oriented
operational visibility surface over approved Morning Briefing public outputs —
without UI productization, HTTP APIs, persistence, workers, Human Review,
AI Decision Engine, or Broker Execution.

## Completed issue chain

| Issue | Deliverable | Pull request | Merge commit |
| --- | --- | --- | --- |
| #85 | Dashboard Foundation | #86 | `c87b1afdca60f0eb4c734c75ed1aeba71de69646` |

Issue document:

- [`issue-dashboard-foundation.md`](issue-dashboard-foundation.md)

Authoritative specification documents (merged with PR #86):

- Planning Gate: [`planning-gate.md`](planning-gate.md)
- Architecture v1: [`docs/architecture/dashboard-architecture-v1.md`](../../architecture/dashboard-architecture-v1.md)
- Governance Decisions #1–#8: [`docs/governance/dashboard/`](../../governance/dashboard/)
- Policy Version v1: [`docs/policy/dashboard-policy-v1.md`](../../policy/dashboard-policy-v1.md)
- Implementation Authorization v1: [`implementation-authorization-v1.md`](implementation-authorization-v1.md)
- Upstream Morning Briefing Policy Version `morning-briefing.policy.v1` (immutable)

## Delivered architecture

- Deterministic Dashboard package under `apps/api/app/dashboard/`.
- Read-only consumption of Morning Briefing public outputs under
  `morning-briefing.policy.v1`.
- Presentation Pipeline semantics under Policy Version `dashboard.policy.v1`.
- Ordering Preservation Policy `preserve_morning_briefing_order.v1`.
- Presentation Selection Policy `include_all_morning_briefing_records.v1`.
- Deterministic identity (`dashboard.identity.v1`) and provenance
  (`dashboard.provenance.v1`) with digest method `canonical_payload_sha256_v1`.
- PIT-safe evaluation with explicit UTC `as_of` and fail-closed cross-PIT /
  unsupported-policy behavior.
- Immutable public contracts and Dashboard public exports.
- Unit, contract, and integration tests; Makefile target `test-api-dashboard`.

## Safety guarantees

- Point-in-time fail-closed behavior for cross-PIT and naive `as_of`.
- Deterministic identity, fingerprints, and exact upstream Morning Briefing
  order preservation (no independent ranking or tie-break).
- No score recomputation and no direct Premarket Scoring consumption.
- No live execution enablement.
- Strategy SDK public API and Market Data contracts preserved.
- No Feature Platform, Morning Briefing, or Premarket Scoring redesign.

## Known exclusions

- Concrete Dashboard UI / product surface (out of scope by Issue #85).
- HTTP APIs, persistence, workers, schedulers, and notifications (out of
  scope by Issue #85).
- Human Review (out of scope by Issue #85; not authorized).
- AI Decision Engine (out of scope by Issue #85; not authorized).
- Broker Execution (out of scope by Issue #85; not authorized).
- Portfolio Management / Risk Engine productization (out of scope by Issue #85).
- Premarket Scoring redesign; Feature Platform / Market Data / Strategy SDK
  expansion; Morning Briefing redesign (out of scope by Issue #85).

## Repository status

- Implementation baseline: `c87b1afdca60f0eb4c734c75ed1aeba71de69646`
- Final Sprint 10 implementation PR: #86 (MERGED)
- Issue #85: CLOSED / COMPLETED
- Feature branch: deleted
- Breaking changes: none claimed for SDK public surface or Market Data
  contracts
- Milestone: still OPEN pending closeout completion
- Release tag: `v0.10.0-sprint10` (PREPARED / **NOT CREATED**)
- GitHub Release: **NOT PUBLISHED**

## Closeout evidence

See [`CLOSEOUT.md`](CLOSEOUT.md).

Release package: [`releases/sprint-10/`](../../../releases/sprint-10/).

Related roadmap: [`ROADMAP.md`](../../../ROADMAP.md).
