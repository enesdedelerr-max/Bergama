# Sprint 5 Release Notes

## Theme

Strategy SDK Hardening.

## Completed

### Strategy SDK Public API Stabilization (Issue #51 / PR #52)

- Documented and froze the root `bergama_strategy_sdk.__all__` surface at exactly
  39 symbols.
- Published public / experimental / internal classification guidance.
- Published compatibility policy for fingerprint-sensitive and version-axis
  changes.
- Added contract tests that lock the public API freeze and import boundary.
- Preserved FeatureSnapshot immutability and fingerprint determinism contracts
  without schema edits.
- Kept package version at `0.1.0`.

## Safety and defaults

- No live execution was enabled.
- No public API expansion beyond the freeze.
- No Broker, Portfolio, Risk, or OMS contract changes as part of Sprint 5.
- Host runtime ownership remains under `apps/api/app/strategy/sdk_runtime/`.

## Breaking Changes

None.

## Backward Compatibility

Maintained.

## Known exclusions

- Feature Platform productization (Sprint 6).
- Premarket Intelligence.
- AI Decision Engine.
- Package or API version bumps.
- Runtime redesign outside the documented freeze.

## References

- Merge commit: `260ffbecb4113040705dc44a768ebf6e75f933ea`
- Issue: https://github.com/enesdedelerr-max/Bergama/issues/51
- PR: https://github.com/enesdedelerr-max/Bergama/pull/52
