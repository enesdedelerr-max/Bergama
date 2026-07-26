# Sprint 6 — Issue #67 — Feature Platform Strategy Host Integration

GitHub Issue: [#67](https://github.com/enesdedelerr-max/Bergama/issues/67)

## Related

- Sprint 6 Planning: [#65](https://github.com/enesdedelerr-max/Bergama/issues/65)
- Foundation: [#66](https://github.com/enesdedelerr-max/Bergama/issues/66)
- Offline Replay Materialization: [#68](https://github.com/enesdedelerr-max/Bergama/issues/68)

## Goal

Wire the existing Feature Platform `BarEvent` → `FeatureSnapshot` materializer
into the Strategy SDK host feature-resolution path behind default-disabled
Feature Platform settings.

## Scope

- Nest `FeaturePlatformSettings` on `AppSettings` (`BERGAMA_FEATURE_PLATFORM__*`)
- `resolve_feature_snapshot_for_strategy_input` host bridge
- Bar catalog registration helper for `FeatureSchemaRegistry`
- Preserve `FeatureAssembler` / legacy assembler path when disabled
- Unit and integration tests

## Out of scope

- Offline/online feature stores
- Derived indicators
- Premarket Intelligence / AI Decision Engine
- Replacing `FeatureAssembler` or `FeatureSchemaRegistry`
- SDK `__all__` or version changes

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
