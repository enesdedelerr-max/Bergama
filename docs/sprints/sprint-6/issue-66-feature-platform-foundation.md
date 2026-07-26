# Sprint 6 — Issue #66 — Feature Platform Foundation (BarEvent → FeatureSnapshot)

GitHub Issue: [#66](https://github.com/enesdedelerr-max/Bergama/issues/66)

## Related

- Sprint 6 Planning: [#65](https://github.com/enesdedelerr-max/Bergama/issues/65)
- Host Integration: [#67](https://github.com/enesdedelerr-max/Bergama/issues/67)
- Offline Replay Materialization: [#68](https://github.com/enesdedelerr-max/Bergama/issues/68)

## Goal

Introduce the Feature Platform bounded context and the first minimum vertical
slice: deterministically project a canonical `BarEvent` into a Sprint 5
compatible `FeatureSnapshot`.

## Scope

- `apps/api/app/features/` bounded context
- Closed bar-field catalog (`bar.open` … `bar.volume`, optional `bar.vwap`)
- Deterministic materializer
- Default-disabled `FeaturePlatformSettings`
- Unit and contract tests

## Out of scope

- Offline/online feature stores
- Indicator computation beyond existing `BarEvent` fields
- Premarket Intelligence, AI Decision Engine
- Broker, Portfolio, Risk, OMS, Human Review
- Strategy SDK `__all__` or version changes

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
