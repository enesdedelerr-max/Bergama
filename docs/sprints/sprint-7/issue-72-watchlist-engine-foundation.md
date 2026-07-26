# Sprint 7 — Issue #72 — Watchlist Engine Foundation

GitHub Issue: [#72](https://github.com/enesdedelerr-max/Bergama/issues/72)

## Authorization

- Planning gate: [#71](https://github.com/enesdedelerr-max/Bergama/issues/71) (approved and closed)
- Theme: Premarket Intelligence — APPROVED
- Watchlist generation — **IN SCOPE**
- First authorized Sprint 7 implementation slice

## Related

- Sprint 7 Planning Gate: [#71](https://github.com/enesdedelerr-max/Bergama/issues/71)
- Feature Platform (prerequisite): Sprint 6 / `apps/api/app/features/`

## Goal

Establish the Premarket Intelligence bounded context and a deterministic,
replayable Watchlist Engine that produces an internal instrument watchlist from
approved candidates and explicit configuration.

## Scope

- `apps/api/app/premarket/` bounded context
- Watchlist data model and generation engine
- Config-driven allowlist inclusion
- Deterministic ordering and rank assignment
- Duplicate rejection (fail-closed)
- Empty-input empty watchlist
- Default-disabled `PremarketSettings`
- Unit, contract, and Market Data identity-boundary integration tests
- `make test-api-premarket`

## Out of scope / deferred

- Catalyst detection or normalization
- Gap scanning
- Premarket scoring / ranking intelligence
- Morning briefing generation
- UI / dashboard / notifications
- Portfolio, risk, broker, execution
- Database persistence / migrations
- Public HTTP API endpoints
- Feature-threshold or Feature Platform–required inclusion rules
- Expansion of `bergama_strategy_sdk.__all__`
- Changes to Market Data ingestion or event contracts

## Bounded-context architecture

```text
apps/api/app/premarket/
  errors.py
  settings.py
  watchlist/
    models.py
    normalize.py
    ordering.py
    engine.py
apps/api/app/core/premarket_settings.py  # nested AppSettings.premarket
```

Watchlist types remain internal to Premarket Intelligence and are not exported
through the Strategy SDK public API.

## Input contract

`WatchlistGenerationRequest`:

- `candidates: tuple[WatchlistCandidate, ...]` (ordered)
- `as_of: datetime` (timezone-aware; normalized to UTC)
- `config: WatchlistConfig`

`WatchlistCandidate`:

- `instrument_key` (canonical identity)
- optional `local_symbol` (display metadata only)

`WatchlistConfig`:

- one or more `WatchlistInclusionRule` allowlists (`rule_id`, `rule_priority`,
  `inclusion_reason`, `allowed_instrument_keys`)
- optional positive `max_size`
- `ordering_policy_id = rule_priority_asc_instrument_key_asc`

Feature Platform snapshots are **not** part of the v1 request model.

## Output contract

`Watchlist`:

- `evaluation_timestamp`
- `entries: tuple[WatchlistEntry, ...]`
- `provenance: WatchlistProvenance`

`WatchlistEntry`:

- `instrument_key`
- optional `local_symbol`
- `evaluation_timestamp`
- `rank` (1-based after deterministic ordering)
- `inclusion_reason`
- `rule_id`

`WatchlistProvenance`:

- `config_fingerprint` (sha256)
- `input_fingerprint` (sha256)
- `ordering_policy_id`
- `source_identifiers` (included instrument keys)

## Identity semantics

- Primary identity: `instrument_key` (aligned with `InstrumentId.instrument_key`)
- Provider tickers are never identity
- `local_symbol` is optional display metadata and may be sourced from an
  effective-dated `InstrumentId` via normalization

## Deterministic ordering

Policy id: `rule_priority_asc_instrument_key_asc`

Total order:

1. `rule_priority` ascending
2. `instrument_key` ascending

When multiple rules match an instrument, the lowest `rule_priority` (then
`rule_id`) wins. Rank is assigned after ordering as `1..N`. Truncation via
`max_size` occurs only after ordering.

## Duplicate / empty / invalid behavior

| Case | Behavior |
|---|---|
| Duplicate `instrument_key` in candidates | `WatchlistDuplicateInstrumentError` |
| Empty candidates | Empty `Watchlist` with provenance (no error) |
| Unsupported candidate type | `WatchlistUnsupportedCandidateError` |
| Naive `as_of` | Validation failure (timezone-aware required) |
| Invalid / non-positive `max_size` | Validation failure |
| Unsupported ordering policy | Validation failure |
| Settings provided and `enabled=False` | `PremarketDisabledError` |

## PIT and replay guarantees

- Explicit `as_of` only; no wall-clock reads in the generation path
- Timestamps normalized with `require_utc_aware`
- Fingerprints via canonical JSON + SHA-256 (`strategy_sha256`)
- Identical request + config ⇒ identical entries, ranks, and fingerprints

## Feature Platform boundary

v1 inclusion is config allowlist only. Feature Platform materializers are not
called and are not required. A future optional adapter may consume approved
Feature Platform outputs without changing this package’s Market Data boundary.

## Market Data boundary

Consumes canonical `InstrumentId` / `instrument_key` semantics. Does not modify
event models, ingestion contracts, PIT quartet rules, or replay ordering.

## Settings

- `PremarketSettings.enabled: bool = False`
- Nested as `AppSettings.premarket` (`BERGAMA_PREMARKET__*`)
- Configured generation fails closed when disabled

## Validation

```bash
make lint
make typecheck
make validate-secrets
make test-api-premarket
make test-api-feature-platform
make test-api-strategy-sdk
make test-api-strategy-engine
git diff --check
```

## Known limitations

- No scoring / dynamic ranking beyond allowlist + priority
- No persistence or API surface
- No Feature Platform–driven inclusion in v1
- `source_identifiers` currently mirror included instrument keys

## Rollback guidance

Revert or delete:

- `apps/api/app/premarket/`
- `apps/api/app/core/premarket_settings.py`
- `AppSettings.premarket` nest in `config.py`
- Premarket tests and `test-api-premarket` Makefile target
- `docs/sprints/sprint-7/issue-72-watchlist-engine-foundation.md`

No database migrations are introduced by this issue.
