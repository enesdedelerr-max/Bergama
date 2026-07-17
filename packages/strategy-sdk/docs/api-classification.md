# Strategy SDK API Classification and Runtime Boundary

## Public

Only the frozen root exports in `bergama_strategy_sdk.__all__`.

See [public-api.md](public-api.md).

## Experimental

`bergama_strategy_sdk.experimental` is a reserved namespace.

- Currently empty / placeholder only
- Not re-exported from the package root
- Not stable
- Not part of Issue #51 compatibility guarantees

## Internal

Internal surfaces include:

- Non-exported SDK helpers (for example serialization helpers)
- Non-exported error types such as `StrategyCancellationError`
- Package-internal metadata such as `PUBLIC_API_VERSION`
- Non-exported semver/parser helpers
- Test harness helpers under `bergama_strategy_sdk.testing`
- All modules under `apps/api/app/strategy/sdk_runtime/`
- Strategy SDK settings (`BERGAMA_STRATEGY_SDK__*`)

Authors must not depend on internal surfaces.

## Host-owned runtime contracts

The following remain host-owned and outside the public SDK. They may be
described here only to clarify ownership:

- `PluginHealth`
- `PluginLifecycle`
- `StrategyBatchExecutionResult`
- Failure / skip / commit result models
- Runtime orchestration, engine, session, registry, budgets, and adapters
- Runtime state persistence

These types must not be imported by strategy authors and must not be added to
the SDK root public API.

The SDK package must continue to have no direct Broker, Portfolio, Risk, or OMS
dependency.
