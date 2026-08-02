# Sprint 9 — Morning Briefing Foundation

## Status

Complete.

Sprint 9 theme is **Morning Briefing Foundation**. Authorized implementation
scope is Issue **#82**, merged on `main` through PR **#83**. The final
implementation merge commit is:

```text
a713bea13b352f35a9390f68ce43081b68587eb9
```

Dashboard, Human Review Workflow, UI, HTTP APIs, persistence, workers,
schedulers, notifications, Broker Execution, and AI Decision Engine remain
deferred or out of scope per Issue **#82** and are not part of the executed
Sprint 9 implementation scope.

Sprint 9 Planning Gate, Morning Briefing Architecture v1, Governance
Decisions #1–#8, Policy Version `morning-briefing.policy.v1`, and
Implementation Authorization v1 are repository-backed under
`docs/sprints/sprint-9/`, `docs/architecture/`, `docs/governance/morning-briefing/`,
and `docs/policy/`. They were merged with PR #83 and are immutable relative to
this closeout.

Governance closeout is recorded in [`CLOSEOUT.md`](CLOSEOUT.md). Release tag
creation for Sprint 9 remains a separate maintainer action after this closeout
is merged and the target commit is verified.

## Objective

Introduce the Morning Briefing Engine under Policy Version
`morning-briefing.policy.v1` as the first authorized downstream consumer of
frozen Premarket Scoring outputs — a deterministic, presentation-oriented
Premarket operator attention context without Dashboard productization, human
review, Decision Engine productization, HTTP APIs, persistence, workers, UI,
notifications, or Broker Execution.

## Completed issue chain

| Issue | Deliverable | Pull request | Merge commit |
| --- | --- | --- | --- |
| #82 | Morning Briefing Foundation | #83 | `a713bea13b352f35a9390f68ce43081b68587eb9` |

Issue document:

- [`issue-morning-briefing-foundation.md`](issue-morning-briefing-foundation.md)

Authoritative specification documents (merged with PR #83):

- Planning Gate: [`planning-gate.md`](planning-gate.md)
- Architecture v1: [`docs/architecture/morning-briefing-architecture-v1.md`](../../architecture/morning-briefing-architecture-v1.md)
- Governance Decisions #1–#8: [`docs/governance/morning-briefing/`](../../governance/morning-briefing/)
- Policy Version v1: [`docs/policy/morning-briefing-policy-v1.md`](../../policy/morning-briefing-policy-v1.md)
- Implementation Authorization v1: [`implementation-authorization-v1.md`](implementation-authorization-v1.md)
- Upstream Premarket Scoring Policy Version `premarket.scoring.policy.v1` (immutable)

## Delivered architecture

- Deterministic Morning Briefing package under
  `apps/api/app/premarket/morning_briefing/`.
- Read-only consumption of Premarket Scoring public outputs under
  `premarket.scoring.policy.v1`.
- Assembly Pipeline semantics under Policy Version
  `morning-briefing.policy.v1`.
- Ordering Preservation Policy `preserve_premarket_scoring_order.v1`.
- Deterministic identity (`morning-briefing.identity.v1`) and provenance
  (`morning-briefing.provenance.v1`) with digest method
  `canonical_payload_sha256_v1`.
- PIT-safe evaluation with explicit UTC `as_of` and fail-closed cross-PIT /
  unsupported-policy behavior.
- Immutable public contracts and Premarket `BRIEFING_*` exports.
- Unit, contract, and integration tests; Makefile target
  `test-api-premarket-morning-briefing` (included in `test-api-premarket`).
- Shared Premarket settings remain fail-closed when supplied and disabled.

## Safety guarantees

- Premarket settings fail closed when supplied and `enabled=False`.
- Point-in-time fail-closed behavior for cross-PIT and naive `as_of`.
- Deterministic identity, fingerprints, and exact upstream score-order
  preservation (no independent ranking or tie-break).
- No live execution enablement.
- Strategy SDK public API and Market Data contracts preserved.
- No Feature Platform redesign.
- Premarket Scoring Foundation remains frozen and is not redesigned.

## Known exclusions

- Dashboard (out of scope by Issue #82; deferred future work).
- Human Review Workflow (out of scope by Issue #82).
- AI Decision Engine (out of scope by Issue #82; remains deferred future work).
- Broker Execution (out of scope by Issue #82).
- UI, HTTP APIs, persistence, workers, schedulers, and notifications (out of
  scope by Issue #82).
- Premarket Scoring redesign; Feature Platform / Market Data / Strategy SDK
  expansion (out of scope by Issue #82).

## Repository status

- Implementation baseline: `a713bea13b352f35a9390f68ce43081b68587eb9`
- Final Sprint 9 implementation PR: #83
- Breaking changes: none claimed for SDK public surface or Market Data
  contracts
- Release tag: `v0.9.0-sprint9` (prepared; **not** created by this closeout)

## Closeout evidence

See [`CLOSEOUT.md`](CLOSEOUT.md).

Release package: [`releases/sprint-9/`](../../../releases/sprint-9/).

Related roadmap: [`ROADMAP.md`](../../../ROADMAP.md).
