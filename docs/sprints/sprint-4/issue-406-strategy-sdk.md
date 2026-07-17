# Sprint 4 — Issue #406 Strategy SDK

## Scope

Introduces the author-facing `bergama-strategy-sdk` package and an explicitly enabled
#406 Strategy SDK Runtime under `apps/api/app/strategy/sdk_runtime/`.

The legacy #401 Strategy Engine path remains the default runtime behavior.

## Included

- Dedicated Strategy SDK package (`packages/strategy-sdk`)
- Immutable `FeatureSnapshot`, explicit state I/O, version axes, fingerprints
- Plugin manifest, permissions, feature schema registry, host feature assembly
- Plugin health lifecycle, execution budgets, per-instance serialization
- Partial `StrategyBatchExecutionResult` recovery on the #406 runtime path
- Separate `BERGAMA_STRATEGY_SDK__*` settings (disabled by default)
- Legacy `StrategyInput` compatibility adapter (runtime-only)

## Excluded

- #407 and downstream strategy product features
- CPU/memory sandboxing
- Automatic state/config migration
- Compatibility shims for removed SDK APIs
- Security sandbox claims

## Enablement

```bash
BERGAMA_STRATEGY_SDK__ENABLED=true
```

Legacy #401 remains available via `BERGAMA_STRATEGY__ENABLED=true` independently.

## Validation

```bash
make test-api-strategy-sdk
make test-api-strategy-engine
make test-api
```
