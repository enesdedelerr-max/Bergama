# Sprint 7 — Issue #76 — Gap Scanner Foundation

GitHub Issue: [#76](https://github.com/enesdedelerr-max/Bergama/issues/76)

## Authorization

- Planning gate: [#71](https://github.com/enesdedelerr-max/Bergama/issues/71) Gap Scanner midpoint amendment
- Gap Scanner — **IN SCOPE** (next authorized slice after Catalyst)
- Prerequisites: Watchlist [#72](https://github.com/enesdedelerr-max/Bergama/issues/72) / Catalyst [#74](https://github.com/enesdedelerr-max/Bergama/issues/74)

## Goal

Compute deterministic overnight gap metrics for Watchlist instruments from
offline canonical `BarEvent` inputs.

## Scope

- `apps/api/app/premarket/gap/`
- Immutable gap contracts
- Selection policy `two_bars_by_close_time_v1`
- Formula: `(current_session_open - previous_session_close) / previous_session_close`
- Decimal quantize policy `decimal_8dp_half_even`
- Ordering: abs(gap) DESC, instrument_key ASC, gap_record_id ASC
- PIT: `known_at > as_of` fails closed
- Unit, contract, integration tests
- `make test-api-premarket-gap`

## Out of scope

- Live market data / providers
- Catalyst enrichment
- Scoring, briefing, UI, workers, persistence, HTTP APIs
- Exchange calendar / RTH session inference
- Strategy SDK or Market Data contract changes

## Inputs

`GapScanRequest`:

- `watchlist: Watchlist` (approved universe)
- `bars: tuple[BarEvent, ...]`
- `as_of` (UTC-aware)
- `config: GapConfig`

## Outputs

`GapCollection` / `GapRecord` / `GapProvenance` with required fields including
`gap_record_id`, prices, `gap_percent`, `gap_direction`, PIT timestamps,
fingerprints, and source identifiers.

## Selection policy (`two_bars_by_close_time_v1`)

Per Watchlist instrument:

1. Reject any bar with `known_at > as_of`
2. Keep bars with matching `instrument_key` and `close_time <= as_of`
3. Sort by `(close_time, source_event_id, provider)`
4. Require ≥ 2 bars; otherwise `GapMissingBarError`
5. Reject duplicate sort keys; otherwise `GapAmbiguousSelectionError`
6. Previous close = `close` of bar `[-2]`
7. Current open = `open` of bar `[-1]`

## Failure behavior

| Case | Behavior |
|---|---|
| Settings disabled | `PremarketDisabledError` |
| Empty Watchlist | Empty collection + provenance |
| Insufficient bars | `GapMissingBarError` |
| Future-known bar | `GapStaleKnownAtError` |
| Non-positive previous close | `GapZeroCloseError` |
| Unsupported event | `GapUnsupportedEventError` |
| Unsupported policy | Validation failure |

## Validation

```bash
make lint
make typecheck
make validate-secrets
make test-api-premarket-gap
make test-api-premarket
make test-api-feature-platform
make test-api-strategy-sdk
make test-api-strategy-engine
git diff --check
```

## Known limitations

- No exchange calendar; two-bar close_time policy is explicit, not RTH-aware
- Catalyst join deferred
- `BarEvent` already rejects non-positive closes at the MD boundary

## Rollback

Remove `apps/api/app/premarket/gap/`, Gap errors/exports, gap tests, Makefile
targets, and this document. No migrations.

## Deferred

Premarket scoring, morning briefing, human review, UI.
