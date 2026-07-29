# Sprint 7 — Issue #74 — Catalyst Ingestion and Normalization Foundation

GitHub Issue: [#74](https://github.com/enesdedelerr-max/Bergama/issues/74)

## Authorization

- Planning gate: [#71](https://github.com/enesdedelerr-max/Bergama/issues/71) midpoint Catalyst authorization
- Theme: Premarket Intelligence — APPROVED
- Catalyst ingestion and normalization — **IN SCOPE** (next authorized slice after Watchlist)
- Prerequisite: Watchlist Engine Foundation [#72](https://github.com/enesdedelerr-max/Bergama/issues/72) / PR [#73](https://github.com/enesdedelerr-max/Bergama/pull/73) / merge `02bf9afe6e3a0a49c0e8758ac57d65e05a30e7d5`

## Related

- Sprint 7 Planning Gate: [#71](https://github.com/enesdedelerr-max/Bergama/issues/71)
- Watchlist Engine: `apps/api/app/premarket/watchlist/`
- Market Data news contract: `apps/api/app/market_data/events/news.py`

## Goal

Establish an internal, deterministic Premarket Catalyst Foundation that converts
approved canonical Market Data `NewsEvent` instances into replayable normalized
catalyst records.

## Scope

- `apps/api/app/premarket/catalyst/` package
- Internal catalyst input/output contracts
- Config-only topic → classification mapping
- Deterministic `catalyst_record_id` via canonical hashing
- Exact semantic duplicate collapse
- Fail-closed source-identity conflicts
- PIT gate: `known_at > as_of` fails closed
- Deterministic total ordering
- Default-disabled `PremarketSettings` fail-closed path
- Unit, contract, and Market Data boundary integration tests
- `make test-api-premarket-catalyst` (also included in `make test-api-premarket`)

## Out of scope / deferred

- Live Benzinga or other provider fetching / network clients
- Background workers / schedulers
- Database persistence / migrations
- Public HTTP API
- NLP / LLM / keyword intelligence beyond explicit config mappings
- Gap scanning, premarket scoring, morning briefing
- Watchlist ranking changes
- UI / notifications
- Broker / execution
- Feature Platform dependency
- Strategy SDK public API expansion
- Market Data ingestion or event contract changes
- `FilingEvent` upstream (v1 is `NewsEvent` only)

## Bounded-context architecture

```text
apps/api/app/premarket/
  errors.py                 # Catalyst* typed errors
  catalyst/
    models.py
    identity.py
    classify.py
    normalize.py
    ordering.py
    engine.py
```

Catalyst types remain internal to Premarket Intelligence and are not exported
through the Strategy SDK public API.

## Upstream event boundary

Approved upstream for this foundation:

- canonical Market Data `NewsEvent` (`MarketEventType.NEWS`) only
- injected fixtures / offline-constructed events for tests and replay

Not authorized:

- live provider HTTP
- mutating Market Data contracts
- introducing a new Market Data event type

## Input contract

`CatalystNormalizationRequest`:

- `events: tuple[NewsEvent, ...]` (ordered)
- `as_of: datetime` (timezone-aware; normalized to UTC)
- `config: CatalystConfig`

`CatalystConfig`:

- one or more `CatalystClassificationRule` mappings
  (`rule_id`, `rule_priority`, `catalyst_type`, `match_topics`)
- `ordering_policy_id = known_at_asc_event_time_asc_type_asc_instrument_key_asc_id_asc`

Classification matches the lowest `rule_priority` (then `rule_id`) whose
`match_topics` intersect the event topics (case-insensitive). Unmatched events
fail closed.

## Output contract

`CatalystCollection`:

- `as_of`
- `records: tuple[CatalystRecord, ...]`
- `provenance: CatalystProvenance`

`CatalystRecord`:

- `catalyst_record_id` (sha256 hex)
- `source_event_id` (optional provider id)
- `source_content_fingerprint` (sha256; equals record id for v1)
- optional `instrument_key` / `local_symbol` (display metadata)
- `catalyst_type`
- `event_time` (from `NewsEvent.occurred_at`)
- `known_at`
- normalization `as_of`
- `source_provider`
- `rule_id`

`CatalystProvenance`:

- `config_fingerprint` / `input_fingerprint` (sha256)
- `ordering_policy_id`
- `source_identifiers` (ordered `catalyst_record_id` values)

## Identity and idempotency

- `catalyst_record_id = strategy_sha256` over a fixed approved field set
  (schema, event type, schema_version, instrument_key, occurred_at, known_at,
  provider, source_event_id or empty, headline, summary, url_ref, topics)
- No random UUIDs
- Exact semantic duplicates (same record id) collapse to one record
- When `source_event_id` is present, conflicting payloads sharing
  `(provider, source_event_id)` fail closed
- Missing provider id → content-derived identity only

## Instrument identity

- Canonical association uses `instrument.instrument_key`
- Provider tickers / `local_symbol` are display metadata only
- NewsEvent always carries an `InstrumentId`; market-wide/unlinked-style keys
  are still valid instrument keys and sort lexicographically

## Deterministic ordering

Policy id: `known_at_asc_event_time_asc_type_asc_instrument_key_asc_id_asc`

Total order:

1. `known_at` ascending
2. `event_time` ascending
3. `catalyst_type` ascending
4. `instrument_key` ascending (sentinel `__unlinked__` if null)
5. `catalyst_record_id` ascending

## Duplicate / empty / invalid behavior

| Case | Behavior |
|---|---|
| Exact semantic duplicate | Collapse to one record |
| Same source identity, different payload | `CatalystIdentityConflictError` |
| Empty events | Empty `CatalystCollection` with provenance |
| Unsupported event type | `CatalystUnsupportedEventError` |
| Naive `as_of` | Validation failure |
| `known_at > as_of` | `CatalystStaleKnownAtError` |
| Unmatched classification | `CatalystClassificationError` |
| Unsupported ordering policy | Validation failure |
| Settings provided and `enabled=False` | `PremarketDisabledError` |

## PIT and replay guarantees

- Explicit `as_of` only; no wall-clock reads in the normalization path
- Timestamps normalized with `require_utc_aware`
- `event_time` and `known_at` remain distinct
- Fingerprints via canonical JSON + SHA-256 (`strategy_sha256`)
- Identical request + config ⇒ identical records, ordering, and fingerprints

## Settings

- `PremarketSettings.enabled: bool = False`
- Nested as `AppSettings.premarket` (`BERGAMA_PREMARKET__*`)
- Configured normalization fails closed when disabled

## Validation

```bash
make lint
make typecheck
make validate-secrets
make test-api-premarket
make test-api-premarket-catalyst
make test-api-feature-platform
make test-api-strategy-sdk
make test-api-strategy-engine
git diff --check
```

## Known limitations

- `NewsEvent` only (no `FilingEvent` in v1)
- Classification is explicit topic mapping only
- No persistence or API surface
- `source_content_fingerprint` currently equals `catalyst_record_id`

## Rollback guidance

Revert or delete:

- `apps/api/app/premarket/catalyst/`
- Catalyst error types in `apps/api/app/premarket/errors.py`
- Catalyst exports from `apps/api/app/premarket/__init__.py`
- Catalyst tests and Makefile targets
- `docs/sprints/sprint-7/issue-74-catalyst-ingestion-normalization-foundation.md`

No database migrations are introduced by this issue.

## Deferred capabilities

- Gap scanner
- Premarket scoring
- Morning briefing
- Human-review workflow
- UI integration
