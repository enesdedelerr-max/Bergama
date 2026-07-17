# Strategy SDK Compatibility Policy

## Supported surface

The only supported compatibility surface is the frozen root package export list
`bergama_strategy_sdk.__all__` documented in [public-api.md](public-api.md).

Submodule import paths are implementation details. They are not promised to
remain stable across releases.

## Version axes

Compatibility validation uses independent version axes:

- `sdk_schema_version`
- `runtime_protocol_version`
- `feature_schema_version`
- `config_schema_version`
- `strategy_version` (strategy identity axis; not overloaded onto the others)

`RuntimeCompatibilityPolicy` and `validate_manifest_compatibility` enforce
fail-closed checks: required and supported versions must share the same major,
and supported must be greater than or equal to required on each compared axis.

Experimental usage is rejected unless the runtime policy explicitly allows it.

## Experimental APIs

`bergama_strategy_sdk.experimental` is reserved and unstable.

- It is not re-exported from the root package.
- It is not part of the frozen public API.
- Manifests that declare experimental usage are fail-closed unless the host
  policy sets `allow_experimental=True`.

## Deprecation

No frozen public symbols are deprecated today.

Future public deprecations must:

1. Keep the symbol in `__all__` until removal is approved.
2. Publish `DeprecationDescriptor` and `MigrationGuidance` metadata.
3. Preserve fingerprint and deterministic behavior unless an explicit major-axis
   change is approved.
4. Document removal timing and replacement.

## Breaking changes

The following are breaking without an approved architecture decision and
version-axis update:

- Adding, removing, renaming, or replacing root `__all__` exports
- Changing FeatureSnapshot, StrategyExecutionOutput, decision, manifest,
  permission, or capability semantics
- Fingerprint-sensitive payload or ordering changes
- Promoting host runtime types into the SDK public API
- Making experimental symbols part of the stable root API

Fingerprint-sensitive changes require explicit versioning and architecture
approval. Silent Sprint 4 contract edits are forbidden.
