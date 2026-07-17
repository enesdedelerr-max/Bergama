# Sprint 5 — Issue #51 — Strategy SDK Public API Stabilization

## Goal

Freeze and document the exact Sprint 4 Strategy SDK root public API without
changing runtime architecture or Sprint 4 public contracts.

## Scope

- Documentation of the frozen root `__all__` surface
- Compatibility policy
- Public / Experimental / Internal classification
- Host-owned runtime boundary documentation
- Contract tests that lock the freeze
- FeatureSnapshot immutability and fingerprint determinism verification
- Strategy protocol / `StrategyExecutionOutput` contract verification
- Regression suites for Strategy SDK and Strategy Engine

## Out of scope

- Runtime redesign or package restructuring
- New SDK features or public export expansion
- Changes to FeatureSnapshot, decisions, manifests, permissions, or capabilities
- Moving host runtime types into the SDK
- Broker, Portfolio, Risk, or OMS integration
- Settings default changes
- Package or API version bumps
- ADR creation

## Frozen public API (exact 39 symbols)

The only supported public API is the existing root package `__all__`:

1. `DeprecationDescriptor`
2. `FeatureSnapshot`
3. `FeatureValue`
4. `MigrationGuidance`
5. `NextStrategyState`
6. `PluginCapability`
7. `PluginPermissions`
8. `PreviousStrategyState`
9. `RuntimeCompatibilityPolicy`
10. `Strategy`
11. `StrategyAction`
12. `StrategyCompatibilityError`
13. `StrategyConfig`
14. `StrategyConfigurationError`
15. `StrategyContractViolation`
16. `StrategyDecision`
17. `StrategyExecutionContext`
18. `StrategyExecutionError`
19. `StrategyExecutionOutput`
20. `StrategyFeatureSchemaError`
21. `StrategyLifecycleError`
22. `StrategyManifestError`
23. `StrategyPermissionError`
24. `StrategyPluginCrash`
25. `StrategyPluginManifest`
26. `StrategyReasonCode`
27. `StrategySdkError`
28. `StrategyStateError`
29. `StrategyTimeoutError`
30. `StrategyValidationError`
31. `StrategyBudgetExceededError`
32. `VersionAxes`
33. `build_decision_id`
34. `configuration_fingerprint`
35. `execution_fingerprint`
36. `feature_fingerprint`
37. `state_fingerprint`
38. `strategy_fingerprint`
39. `validate_manifest_compatibility`

Not public:

- `StrategyCancellationError`
- `PUBLIC_API_VERSION`
- Host runtime types (`PluginHealth`, `PluginLifecycle`,
  `StrategyBatchExecutionResult`, engine, session, registry, budgets, adapters)

Submodule import paths are implementation details and are not
compatibility-guaranteed.

## Runtime ownership boundary

Remain host-owned under `apps/api/app/strategy/sdk_runtime/` and related
settings:

- Plugin health and lifecycle
- Batch execution results and failure / skip / commit models
- Runtime orchestration, engine, session, registry, budgets, adapters
- Runtime state persistence
- `BERGAMA_STRATEGY_SDK__*` settings

The SDK must retain no direct access to Broker, Portfolio, Risk, or OMS.

## Public / Experimental / Internal classification

- **Public:** the frozen root `__all__` list above
- **Experimental:** `bergama_strategy_sdk.experimental` (reserved/empty; not
  re-exported; not stable)
- **Internal:** non-`__all__` SDK helpers, serialization helpers, non-exported
  semver helpers, all host `sdk_runtime` modules, and Strategy SDK settings

## Compatibility policy

See [`packages/strategy-sdk/docs/compatibility.md`](../../../packages/strategy-sdk/docs/compatibility.md).

Summary:

- Only root `__all__` is the supported compatibility surface
- Existing version-axis fail-closed validation remains in force
- Experimental APIs are opt-in and unstable
- No public symbols are deprecated today
- Fingerprint-sensitive changes require explicit versioning and architecture
  approval

## Acceptance criteria mapping

| Criterion | Evidence |
| --- | --- |
| Public SDK surface documented | `packages/strategy-sdk/docs/public-api.md` |
| Public exports frozen | Exact `__all__` contract test |
| Internal APIs hidden from root | Internal exclusion contract tests |
| Immutable FeatureSnapshot preserved | Model/determinism tests; no schema edits |
| Deterministic replay tests pass | `make test-api-strategy-sdk` / engine suites |
| Plugin lifecycle/health documented as host-owned | Classification / boundary docs |
| Compatibility policy published | `packages/strategy-sdk/docs/compatibility.md` |
| Sprint 4 consumers unchanged | No production contract changes |
| No Sprint 4 contract regressions | Focused regression suites green |

## Test evidence expectations

Run and record:

```bash
make lint
make typecheck
make validate-secrets
make test-api-strategy-sdk
make test-api-strategy-engine
git diff --check
```
