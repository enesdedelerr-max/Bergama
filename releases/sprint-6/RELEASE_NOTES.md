# Sprint 6 Release Notes

## Theme

Feature Platform.

## Completed

### Planning (Issue #65)

- Approved Sprint 6 theme: Feature Platform.
- Documented sequencing for Foundation → Host Integration → Offline Replay
  Materialization, with Premarket Intelligence and AI Decision Engine deferred.

### Foundation (Issue #66)

- Added Feature Platform bounded context under `apps/api/app/features/`.
- Deterministic `BarEvent` → `FeatureSnapshot` materialization.
- Closed bar catalog: `bar.open`, `bar.high`, `bar.low`, `bar.close`,
  `bar.volume`, optional `bar.vwap`.

### Strategy Host Integration (Issue #67)

- Nested `FeaturePlatformSettings` on `AppSettings`
  (`BERGAMA_FEATURE_PLATFORM__*`).
- Host resolution bridge for strategy inputs when Feature Platform is enabled.
- Feature Platform remains **disabled by default**; legacy assembler path
  preserved when disabled.

### Offline Replay Materialization (Issue #68)

- Ordered `BarEvent` sequence → ordered `FeatureSnapshot` sequence via
  `materialize_bar_feature_snapshot_sequence`.
- Deterministic ordered fingerprints; fail-closed on non-bar inputs.
- No persistence, network, database, Kafka, or Iceberg access in this path.

## Safety and defaults

- Feature Platform disabled by default.
- No live execution enablement.
- Strategy SDK public `__all__` freeze and package version `0.1.0` preserved.
- Non-`BarEvent` inputs fail closed.

## Validation evidence

```bash
make lint
make typecheck
make validate-secrets
make test-api-feature-platform
make test-api-strategy-sdk
make test-api-strategy-engine
git diff --check
```

## Breaking Changes

None to the frozen Strategy SDK public API.

## Backward Compatibility

Maintained for Sprint 5 FeatureSnapshot / FeatureValue contracts.

## Known limitations

- Not a Feature Store.
- No feature persistence or Iceberg feature writers.
- No offline serving or online feature store.
- No derived indicators beyond existing bar fields.
- Market Data replay is not a mandatory Feature Platform path.

## Risks

| Risk | Mitigation |
| --- | --- |
| Accidental Feature Store scope creep | Explicit exclusions in closeout and issue docs |
| Default-on Feature Platform | Settings default disabled; fail-closed |
| Premarket / Decision Engine early start | Deferred to Sprint 7 / Sprint 8 |

## Rollback guidance

- Documentation-only closeout: revert the governance commit.
- Implementation rollback: use normal change control against PR #69 /
  `a04b9e5d5b5673a3f4f2022159915b520995bf06`.

## Explicit exclusions

- Feature Store
- Persistence
- Online serving
- Additional indicators
- Premarket Intelligence
- AI Decision Engine

## References

- Merge commit: `a04b9e5d5b5673a3f4f2022159915b520995bf06`
- Issues: #65, #66, #67, #68
- PR: https://github.com/enesdedelerr-max/Bergama/pull/69
