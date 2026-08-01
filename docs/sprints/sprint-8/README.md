# Sprint 8 — Premarket Scoring Foundation

## Status

Complete.

Sprint 8 theme is **Premarket Scoring Foundation**. Authorized implementation
scope is Issue **#78**, merged on `main` through PR **#79**. The final
implementation merge commit is:

```text
dedccab35d3238f6cc9840689ca61a99cc454ce6
```

Morning Briefing, Human Review Workflow, UI, HTTP APIs, persistence, workers,
live providers, and AI Decision Engine remain deferred or out of scope per
Issue **#78** and are not part of the executed Sprint 8 implementation scope.

Governance Decisions #1–#12, Policy Version v1, and Premarket Scoring Engine
Architecture v1 are repository-backed under `docs/governance/`,
`docs/policy/`, and `docs/architecture/`. They were merged with PR #79 and are
immutable relative to this closeout.

Governance closeout is recorded in [`CLOSEOUT.md`](CLOSEOUT.md). Release tag
creation for Sprint 8 remains a separate maintainer action after this closeout
is merged and the target commit is verified.

## Objective

Introduce the Premarket Scoring Engine under Policy Version
`premarket.scoring.policy.v1` as a Premarket-internal deterministic attention /
ordering-priority signal over an approved Watchlist universe — without
briefing, human review, Decision Engine productization, HTTP APIs,
persistence, workers, UI, or live providers.

## Completed issue chain

| Issue | Deliverable | Pull request | Merge commit |
| --- | --- | --- | --- |
| #78 | Premarket Scoring Foundation | #79 | `dedccab35d3238f6cc9840689ca61a99cc454ce6` |

Issue document:

- [`issue-78-premarket-scoring-foundation.md`](issue-78-premarket-scoring-foundation.md)

Authoritative specification documents (merged with PR #79):

- Governance Decisions #1–#12: [`docs/governance/`](../../governance/)
- Policy Version v1: [`docs/policy/premarket-scoring-policy-v1.md`](../../policy/premarket-scoring-policy-v1.md)
- Architecture v1: [`docs/architecture/premarket-scoring-engine-architecture-v1.md`](../../architecture/premarket-scoring-engine-architecture-v1.md)
- Gap conflict scope rationale: [`docs/architecture/premarket-scoring-gap-conflict-scope.md`](../../architecture/premarket-scoring-gap-conflict-scope.md)

## Delivered architecture

- Deterministic Premarket Scoring package under
  `apps/api/app/premarket/scoring/`.
- Watchlist-required scoring with authorized optional Catalyst and Gap inputs.
- Policy Version v1 Feature Specs: `watchlist_rank.v1`, `gap_magnitude.v1`,
  `catalyst_presence.v1`.
- Weight Profile `default_v1` (`0.50` / `0.30` / `0.20`) with no weight
  redistribution on missing optional features.
- Decimal-only scoring with quantize policy `decimal_8dp_half_even`.
- Deterministic identity (`premarket.score.identity.v1`), provenance, and
  ordering (`score_desc_instrument_key_asc_score_record_id_asc`).
- PIT-safe evaluation with explicit UTC `as_of` and fail-closed future-known
  evidence.
- Shared Premarket settings remain fail-closed when supplied and disabled.

## Safety guarantees

- Premarket settings fail closed when supplied and `enabled=False`.
- Point-in-time fail-closed behavior for future-known inputs.
- Deterministic identity, fingerprints, and total ordering.
- No live execution enablement.
- Strategy SDK public API and Market Data contracts preserved.
- No Feature Platform redesign.

## Known exclusions

- Morning Briefing (out of scope by Issue #78).
- Human Review Workflow (out of scope by Issue #78).
- AI Decision Engine (out of scope by Issue #78; remains deferred future work).
- UI, HTTP APIs, persistence, workers, and live providers (out of scope by
  Issue #78).

## Repository status

- Implementation baseline: `dedccab35d3238f6cc9840689ca61a99cc454ce6`
- Final Sprint 8 implementation PR: #79
- Breaking changes: none claimed for SDK public surface or Market Data
  contracts
- Release tag: `v0.8.0-sprint8` (prepared; create only after closeout merge)

## Closeout evidence

See [`CLOSEOUT.md`](CLOSEOUT.md).

Release package: [`releases/sprint-8/`](../../../releases/sprint-8/).

Related roadmap: [`ROADMAP.md`](../../../ROADMAP.md).
