# Sprint 6 — Feature Platform

## Status

Complete.

Sprint 6 theme is **Feature Platform**. Premarket Intelligence and AI Decision
Engine remain planned for later sprints and are not part of the executed
Sprint 6 implementation scope.

Planning issue **#65** defined the theme and sequencing. Implementation issues
**#66–#68** are merged on `main` through PR **#69**:

```text
a04b9e5d5b5673a3f4f2022159915b520995bf06
```

Governance closeout is recorded in [`CLOSEOUT.md`](CLOSEOUT.md). Release tag
creation for Sprint 6 remains a separate maintainer action after this closeout
is merged and the target commit is verified.

## Objective

Introduce the Feature Platform bounded context with deterministic
`BarEvent` → `FeatureSnapshot` materialization, optional Strategy Host
resolution behind default-disabled settings, and offline/replay batch
materialization — without feature persistence, online serving, Premarket, or
Decision Engine productization.

## Completed issue chain

| Issue | Deliverable | Pull request | Merge commit |
| --- | --- | --- | --- |
| #65 | Backlog Definition and Theme Sequencing | (planning) | — |
| #66 | Feature Platform Foundation | #69 | `a04b9e5d5b5673a3f4f2022159915b520995bf06` |
| #67 | Feature Platform Strategy Host Integration | #69 | `a04b9e5d5b5673a3f4f2022159915b520995bf06` |
| #68 | Feature Platform Offline Replay Materialization | #69 | `a04b9e5d5b5673a3f4f2022159915b520995bf06` |

Issue documents:

- [`issue-65-backlog-definition-and-theme-sequencing.md`](issue-65-backlog-definition-and-theme-sequencing.md)
- [`issue-66-feature-platform-foundation.md`](issue-66-feature-platform-foundation.md)
- [`issue-67-feature-platform-host-integration.md`](issue-67-feature-platform-host-integration.md)
- [`issue-68-feature-platform-offline-replay-materialization.md`](issue-68-feature-platform-offline-replay-materialization.md)

## Delivered architecture

- Deterministic projection: canonical `BarEvent` → Sprint 5-compatible
  `FeatureSnapshot` / `FeatureValue`.
- Closed bar catalog feature IDs:
  - `bar.open`
  - `bar.high`
  - `bar.low`
  - `bar.close`
  - `bar.volume`
  - optional `bar.vwap`
- Strategy Host resolution bridge (`resolve_feature_snapshot_for_strategy_input`)
  nested under `AppSettings.feature_platform`, **disabled by default**.
- Offline/replay ordered batch materialization via
  `materialize_bar_feature_snapshot_sequence` (in-memory; no persistence).

## Safety guarantees

- Feature Platform remains disabled by default.
- Non-`BarEvent` inputs fail closed.
- Sprint 5 `FeatureSnapshot` / `FeatureValue` contracts preserved.
- `bergama_strategy_sdk.__all__` and package version `0.1.0` unchanged.
- No live execution enablement.

## Known exclusions

- Feature Store productization.
- Feature persistence / feature Iceberg writers.
- Offline serving APIs and online feature store.
- Derived indicators beyond existing `BarEvent` fields.
- Premarket Intelligence.
- AI Decision Engine.
- Mandatory Feature Platform wiring into Market Data `ReplayEngine`.

## Repository status

- Implementation baseline: `a04b9e5d5b5673a3f4f2022159915b520995bf06`
- Final Sprint 6 implementation PR: #69
- Breaking changes: none claimed for SDK public surface
- Release tag: prepared as `v0.6.0-sprint6`; **not created**

## Closeout evidence

See [`CLOSEOUT.md`](CLOSEOUT.md).

Release package: [`releases/sprint-6/`](../../../releases/sprint-6/).

Related roadmap: [`ROADMAP.md`](../../../ROADMAP.md).
