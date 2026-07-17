# Bergama Strategy SDK

Author-facing contracts for strategy plugins.

This package defines the stable Strategy SDK surface introduced in Sprint 4
(#406) and frozen by Sprint 5 Issue #51.

Runtime orchestration remains host-owned under
`apps/api/app/strategy/sdk_runtime/`. Authors must not import host runtime,
Broker, Portfolio, Risk, or OMS modules.

## Stable public API

**Only the root package exports in `bergama_strategy_sdk.__all__` are stable.**

Import from the package root:

```python
from bergama_strategy_sdk import (
    FeatureSnapshot,
    FeatureValue,
    Strategy,
    StrategyConfig,
    StrategyDecision,
    StrategyExecutionContext,
    StrategyExecutionOutput,
    StrategyAction,
    StrategyReasonCode,
    PreviousStrategyState,
    NextStrategyState,
)
```

Minimal authoring sketch:

```python
from bergama_strategy_sdk import (
    FeatureSnapshot,
    StrategyConfig,
    StrategyExecutionContext,
    StrategyExecutionOutput,
    PreviousStrategyState,
)


class ExampleStrategy:
    async def execute(
        self,
        *,
        previous_state: PreviousStrategyState | None,
        feature_snapshot: FeatureSnapshot,
        context: StrategyExecutionContext,
        config: StrategyConfig,
    ) -> StrategyExecutionOutput:
        raise NotImplementedError
```

## Warnings

- Submodule import paths (for example `bergama_strategy_sdk.features`) are
  implementation details and are **not** compatibility-guaranteed.
- Host-owned types such as `PluginHealth`, `PluginLifecycle`, and
  `StrategyBatchExecutionResult` are **not** SDK public API.
- `bergama_strategy_sdk.experimental` is reserved and unstable. It is not part
  of the frozen root API.

## Documentation

- [Public API reference](docs/public-api.md)
- [Compatibility policy](docs/compatibility.md)
- [API classification and runtime boundary](docs/api-classification.md)
- [Sprint 5 Issue #51](../../docs/sprints/sprint-5/issue-51-strategy-sdk-public-api-stabilization.md)

Issue tracking: GitHub #51.
