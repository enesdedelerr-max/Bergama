# Sprint 6 — Issue #68 — Feature Platform Offline Replay Materialization

GitHub Issue: [#68](https://github.com/enesdedelerr-max/Bergama/issues/68)

## Related

- Sprint 6 Planning: [#65](https://github.com/enesdedelerr-max/Bergama/issues/65)
- Foundation: [#66](https://github.com/enesdedelerr-max/Bergama/issues/66)
- Host Integration: [#67](https://github.com/enesdedelerr-max/Bergama/issues/67)

## Goal

Add the smallest Feature Platform offline/replay batch materialization API:
ordered `BarEvent` sequence → ordered `FeatureSnapshot` sequence, reusing
`materialize_bar_feature_snapshot` and the closed bar catalog.

This is **not** an offline feature store, feature persistence layer, Iceberg
feature writer, or online serving path.

## Scope

- `materialize_bar_feature_snapshot_sequence` under `apps/api/app/features/`
- Empty / single / multi-event sequence behavior
- Deterministic ordered fingerprints
- Fail-closed when any input is not a `BarEvent` (no partial output)
- Unit and contract tests with pinned fixtures
- Feature Platform remains disabled by default

## Out of scope

- Offline feature persistence / feature Iceberg tables or writers
- Offline serving APIs / online feature store
- Wiring Market Data `ReplayEngine` as a mandatory Feature Platform path
- Derived indicators or bar catalog expansion
- Premarket Intelligence / AI Decision Engine
- Broker, Portfolio, Risk, OMS, Human Review, Research, MLOps
- `bergama_strategy_sdk.__all__` or package version changes

## Behavior

| Input | Result |
|---|---|
| Empty sequence | Empty tuple; no failure |
| Single `BarEvent` | One `FeatureSnapshot` via existing materializer |
| Ordered multi-`BarEvent` | Snapshots in the same order; Decimal values preserved |
| Any non-`BarEvent` | `FeaturePlatformUnsupportedEventError` before emitting results |
| `settings.enabled=False` | `FeaturePlatformDisabledError` (same as single-bar) |

## Validation

```bash
make lint
make typecheck
make validate-secrets
make test-api-feature-platform
make test-api-strategy-sdk
make test-api-strategy-engine
git diff --check
```

Plus focused offline/replay tests:

```bash
cd apps/api && uv run pytest -q \
  tests/unit/test_feature_platform_offline_replay.py \
  tests/contract/test_feature_platform_offline_replay_contract.py
```
