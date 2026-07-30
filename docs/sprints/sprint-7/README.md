# Sprint 7 — Premarket Intelligence

## Status

Complete.

Sprint 7 theme is **Premarket Intelligence**. Authorized foundation slices are
Watchlist Engine, Catalyst Ingestion and Normalization, and Gap Scanner.
Premarket Scoring, Morning Briefing, Human Review Workflow, and UI remain
deferred or out of scope per Issue **#71** and are not part of the executed
Sprint 7 implementation scope.

Planning issue **#71** defined the theme and sequencing. Implementation issues
**#72**, **#74**, and **#76** are merged on `main` through PRs **#73**,
**#75**, and **#77**. The final implementation merge commit is:

```text
3b8358e728555bc17da87786b3a2f41792559433
```

Governance closeout is recorded in [`CLOSEOUT.md`](CLOSEOUT.md). Release tag
`v0.7.0-sprint7` is created as part of Sprint 7 governance closeout.

## Objective

Introduce Premarket Intelligence foundations that produce deterministic,
replay-safe Watchlist, Catalyst, and Gap records from offline Market Data
inputs and explicit configuration — without scoring, briefing, UI, persistence,
HTTP APIs, workers, or live providers.

## Completed issue chain

| Issue | Deliverable | Pull request | Merge commit |
| --- | --- | --- | --- |
| #71 | Premarket Intelligence Planning and Implementation Gate | (planning) | — |
| #72 | Watchlist Engine Foundation | #73 | `02bf9afe6e3a0a49c0e8758ac57d65e05a30e7d5` |
| #74 | Catalyst Ingestion and Normalization Foundation | #75 | `05f38e841972793b4111fa1a165922dab81e925a` |
| #76 | Gap Scanner Foundation | #77 | `3b8358e728555bc17da87786b3a2f41792559433` |

Issue documents:

- [`issue-72-watchlist-engine-foundation.md`](issue-72-watchlist-engine-foundation.md)
- [`issue-74-catalyst-ingestion-normalization-foundation.md`](issue-74-catalyst-ingestion-normalization-foundation.md)
- [`issue-76-gap-scanner-foundation.md`](issue-76-gap-scanner-foundation.md)

## Delivered architecture

- Deterministic Watchlist generation from explicit candidates and rules.
- Deterministic Catalyst normalization from offline Market Data news events.
- Deterministic Gap Scanner over Watchlist instruments and offline `BarEvent`s
  using selection policy `two_bars_by_close_time_v1`.
- Shared Premarket settings nested under application settings, **disabled by
  default**.

## Safety guarantees

- Premarket remains disabled by default.
- Point-in-time fail-closed behavior for future-known inputs.
- Deterministic identity, fingerprints, and ordering.
- No live execution enablement.
- Strategy SDK public `__all__` and Market Data contracts preserved.

## Known exclusions

- Premarket Scoring (deferred by Issue #71).
- Morning Briefing generation and API (deferred by Issue #71).
- Human Review Workflow (deferred by Issue #71).
- UI integration (out of scope by Issue #71).
- Live providers, workers, persistence, and public Premarket HTTP APIs for the
  authorized foundation slices.
- AI Decision Engine.

## Repository status

- Implementation baseline: `3b8358e728555bc17da87786b3a2f41792559433`
- Final Sprint 7 implementation PR: #77
- Breaking changes: none claimed for SDK public surface or Market Data
  contracts
- Release tag: `v0.7.0-sprint7`

## Closeout evidence

See [`CLOSEOUT.md`](CLOSEOUT.md).

Release package: [`releases/sprint-7/`](../../../releases/sprint-7/).

Related roadmap: [`ROADMAP.md`](../../../ROADMAP.md).
