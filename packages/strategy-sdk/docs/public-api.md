# Strategy SDK Public API Reference

Issue #51 freezes the Sprint 4 Strategy SDK root public API.

The only supported public surface is `bergama_strategy_sdk.__all__`.

Submodule paths are implementation details and must not be treated as a second
stable API.

## Frozen root exports (exact 39 symbols)

### Authoring protocol

- `Strategy`
- `StrategyExecutionOutput`

### Feature and execution inputs

- `FeatureSnapshot`
- `FeatureValue`
- `StrategyExecutionContext`
- `StrategyConfig`
- `PreviousStrategyState`

### Decisions and state outputs

- `StrategyDecision`
- `StrategyAction`
- `StrategyReasonCode`
- `NextStrategyState`

### Plugin declaration and versions

- `StrategyPluginManifest`
- `PluginCapability`
- `PluginPermissions`
- `VersionAxes`

### Compatibility

- `RuntimeCompatibilityPolicy`
- `validate_manifest_compatibility`

### Fingerprints

- `build_decision_id`
- `configuration_fingerprint`
- `execution_fingerprint`
- `feature_fingerprint`
- `state_fingerprint`
- `strategy_fingerprint`

### Errors

- `StrategySdkError`
- `StrategyValidationError`
- `StrategyConfigurationError`
- `StrategyCompatibilityError`
- `StrategyTimeoutError`
- `StrategyContractViolation`
- `StrategyPluginCrash`
- `StrategyExecutionError`
- `StrategyBudgetExceededError`
- `StrategyStateError`
- `StrategyManifestError`
- `StrategyFeatureSchemaError`
- `StrategyPermissionError`
- `StrategyLifecycleError`

### Deprecation metadata

- `DeprecationDescriptor`
- `MigrationGuidance`

## Explicit exclusions

Not part of the frozen public API:

- `StrategyCancellationError`
- `PUBLIC_API_VERSION`
- `bergama_strategy_sdk.experimental` contents
- Host runtime types (`PluginHealth`, `PluginLifecycle`,
  `StrategyBatchExecutionResult`, engine, session, registry, budgets, adapters)
- Serialization helpers and other non-exported package internals

Adding, removing, or renaming root exports requires a new approved issue and
architecture review.
