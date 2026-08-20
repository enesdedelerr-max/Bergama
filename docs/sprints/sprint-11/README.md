# Sprint 11 — Human Review Foundation

## Status

COMPLETE.

Sprint 11 theme is **Human Review Foundation**. Authorized implementation
scope is Issue **#89**, merged on `main` through PR **#90**. The
implementation baseline / rollback reference is:

```text
baf1ae03312418cfe6a17d8615ccfec62d14f8c0
```

| Field | Value |
| --- | --- |
| Sprint | Sprint 11 |
| Theme | Human Review Foundation |
| Status | COMPLETE |
| Planning Gate ID | `sprint-11.planning-gate` |
| Planning | APPROVED |
| Architecture | APPROVED (`human-review.architecture.v1`) |
| Governance | COMPLETE (Decisions #1–#8 RESOLVED) |
| Policy | APPROVED (`human-review.policy.v1`) |
| Implementation Authorization | APPROVED (`human-review.implementation-authorization.v1`) |
| Implementation Issue | [#89](https://github.com/enesdedelerr-max/Bergama/issues/89) — CLOSED / COMPLETED |
| Implementation PR | [#90](https://github.com/enesdedelerr-max/Bergama/pull/90) — MERGED |
| Implementation baseline | `baf1ae03312418cfe6a17d8615ccfec62d14f8c0` |
| Feature branch | `feature/sprint11-89-human-review-foundation` — deleted |
| Milestone | Sprint 11 — still **OPEN** pending closeout completion |
| Release tag | `v0.11.0-sprint11` — PREPARED / **NOT CREATED** |
| GitHub Release | **NOT PUBLISHED** |

AI Decision Engine, Broker Execution, UI, HTTP APIs, persistence, workers,
schedulers, notifications, reviewer-role management, and workflow expansion
remain deferred or out of scope per Issue **#89** and are not part of the
executed Sprint 11 implementation scope.

Sprint 11 Planning Gate, Human Review Architecture v1, Governance Decisions
#1–#8, Policy Version `human-review.policy.v1`, and Implementation
Authorization v1 are repository-backed under `docs/sprints/sprint-11/`,
`docs/architecture/`, `docs/governance/human-review/`, and `docs/policy/`.
They were merged with PR #90 and are immutable relative to this closeout.

Governance closeout is recorded in [`CLOSEOUT.md`](CLOSEOUT.md). Release tag
creation for Sprint 11 remains a separate maintainer action after this closeout
is merged. Preferred tag target is the closeout merge tip on `main`, not the
implementation baseline.

## Objective

Introduce the Human Review bounded context under Policy Version
`human-review.policy.v1` as a deterministic, auditable, human-authority surface
over approved Dashboard public outputs — without UI productization, HTTP APIs,
persistence, workers, AI Decision Engine, or Broker Execution.

## Completed issue chain

| Issue | Deliverable | Pull request | Merge commit |
| --- | --- | --- | --- |
| #89 | Human Review Foundation | #90 | `baf1ae03312418cfe6a17d8615ccfec62d14f8c0` |

Issue document:

- [`issue-human-review-foundation.md`](issue-human-review-foundation.md)

Authoritative specification documents (merged with PR #90):

- Planning Gate: [`planning-gate.md`](planning-gate.md)
- Architecture v1: [`docs/architecture/human-review-architecture-v1.md`](../../architecture/human-review-architecture-v1.md)
- Governance Decisions #1–#8: [`docs/governance/human-review/`](../../governance/human-review/)
- Policy Version v1: [`docs/policy/human-review-policy-v1.md`](../../policy/human-review-policy-v1.md)
- Implementation Authorization v1: [`implementation-authorization-v1.md`](implementation-authorization-v1.md)
- Upstream Dashboard Policy Version `dashboard.policy.v1` (immutable)

## Delivered architecture

- Deterministic Human Review package under `apps/api/app/human_review/`.
- Read-only consumption of Dashboard public outputs under `dashboard.policy.v1`.
- Human Review Pipeline semantics under Policy Version `human-review.policy.v1`.
- Ordering Preservation Policy `preserve_dashboard_order.v1`.
- Presentation Preservation Policy
  `include_all_dashboard_presentation_records.v1`.
- Explicit Human Attestation Policy
  `explicit_human_attestation.recorded_input.v1`.
- Deterministic identity (`human-review.identity.v1`), provenance
  (`human-review.provenance.v1`), and history binding
  (`human-review.history.v1`) with digest method `canonical_payload_sha256_v1`.
- PIT-safe evaluation with explicit UTC `as_of` and fail-closed cross-PIT /
  unsupported-policy behavior.
- Immutable public contracts and Human Review public exports.
- Unit, contract, and integration tests; Makefile target
  `test-api-human-review`.

## Safety guarantees

- Point-in-time fail-closed behavior for cross-PIT and naive `as_of`.
- Deterministic identity, fingerprints, history binding, and exact upstream
  Dashboard order preservation (no independent ranking or tie-break).
- Explicit human attestation required; no fabricated, inferred, auto-approved,
  or auto-rejected authority.
- No Dashboard regeneration and no direct Morning Briefing or Premarket Scoring
  consumption.
- No live execution enablement.
- Strategy SDK public API and Market Data contracts preserved.
- No Feature Platform, Dashboard, Morning Briefing, or Premarket Scoring
  redesign.

## Known exclusions

- Concrete Human Review UI / product surface (out of scope by Issue #89).
- HTTP APIs, persistence, workers, schedulers, and notifications (out of
  scope by Issue #89).
- Reviewer-role management and workflow expansion (out of scope by Issue #89).
- AI Decision Engine (out of scope by Issue #89; not authorized).
- Broker Execution (out of scope by Issue #89; not authorized).
- Portfolio Management / Risk Engine productization (out of scope by Issue #89).
- Dashboard redesign; Morning Briefing redesign; Premarket Scoring redesign;
  Feature Platform / Market Data / Strategy SDK expansion (out of scope by
  Issue #89).

## Repository status

- Implementation baseline: `baf1ae03312418cfe6a17d8615ccfec62d14f8c0`
- Final Sprint 11 implementation PR: #90 (MERGED)
- Issue #89: CLOSED / COMPLETED
- Feature branch: deleted
- Breaking changes: none claimed for SDK public surface or Market Data
  contracts
- Milestone: still OPEN pending closeout completion
- Release tag: `v0.11.0-sprint11` (PREPARED / **NOT CREATED**)
- GitHub Release: **NOT PUBLISHED**

## Closeout evidence

See [`CLOSEOUT.md`](CLOSEOUT.md).

Release package: [`releases/sprint-11/`](../../../releases/sprint-11/).

Related roadmap: [`ROADMAP.md`](../../../ROADMAP.md).
