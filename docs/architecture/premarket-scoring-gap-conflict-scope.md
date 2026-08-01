# Premarket Scoring — Gap Conflict Failure Scope

Status: Implementation rationale (does not modify Architecture v1 or Policy Version v1)

## Question

Policy Version v1 Duplicate / Conflict tables state that duplicate or conflicting usable Gap
records for one instrument shall **fail closed for that instrument**.

The Premarket Scoring Engine raises `ScoreConflictError` and aborts the **entire evaluation**.

## Decision

Retain **evaluation-scoped** fail-closed abort for Gap duplicate/conflict conditions under
Policy Version `premarket.scoring.policy.v1`.

## Rationale

1. Policy Version v1 does not define a partial-success `ScoreCollection` contract, skip marker,
   or per-instrument failure record for conflicted instruments.
2. Architecture v1 requires: "No partial silent success for prohibited conditions."
   Omitting a Watchlist instrument from the emitted collection without an explicit failure
   artifact would be observationally indistinguishable from "never scored," which is unsafe.
3. Evaluation abort is a strict fail-closed supersets of instrument failure: the conflicted
   instrument never receives a score, and no sibling scores are emitted under unresolved
   conflicting Gap evidence in the same PIT evaluation.
4. Governance Decision #7 (no silent discard / no silent reconciliation) is preserved.

## Non-change

This rationale does **not** alter:

- Repository Governance Decisions #1–#12
- Policy Version v1 formulas, weights, ordering, or Feature Specs
- Premarket Scoring Engine Architecture v1 package layout or ports

A future Policy Version may introduce an explicit instrument-scoped failure envelope; until
then, evaluation abort remains the binding runtime behavior.
