# Sprint 3 — Market Data Plane

## Status

✅ **Sprint 2** complete on `main` (`v0.2.0-sprint2`, gate GO).  
✅ **Issue #301** Canonical Market Data Contract — complete on `main`.  
✅ **Issue #302** Polygon Historical Connector — complete on `main`.  
✅ **Issue #303** Polygon Realtime Connector — stocks WebSocket T/Q/AM transport.  
✅ **Issue #304A** Finnhub Fundamentals Connector — profile2 + basic financials whitelist.  
✅ **Issue #304B** FRED Macro Connector — series + observations → MacroEvent.  
✅ **Issue #304C** SEC EDGAR Filings Connector — submissions → FilingEvent.  
✅ **Issue #304D** Benzinga News Connector — complete on `main`.  
✅ **Issue #304E** Cross-Provider Connector Contract Tests — complete on `main`.  
⏳ **Issue #305** Market Data Orchestrator — in progress on feature branch.

## Goal

Ingest provider market data into provider-independent, point-in-time-safe
canonical contracts. Kafka publishing and Iceberg writes remain later issues.

## Issue chain (first slice)

1. ✅ **#301** Canonical Market Data Contract
2. ✅ **#302** Polygon Historical Connector
3. ✅ **#303** Polygon Realtime Connector
4. ✅ **#304A** Finnhub Fundamentals Connector
5. ✅ **#304B** FRED Macro Connector
6. ✅ **#304C** SEC EDGAR Filings Connector
7. ✅ **#304D** Benzinga News Connector
8. ✅ **#304E** Cross-Provider Connector Contract Tests
9. ⏳ **#305** Market Data Orchestrator
10. Later: Kafka publish, Iceberg, …

## #305 scope

Canonical-event pipeline after connectors:

`CanonicalMarketEvent → validate → PIT → quality → per-stream acquire → dedup reserve → route → bounded in-flight admission → PublishPort → dedup commit/release → stream release`

Settings (minimal): `enabled`, `dry_run`, `pipeline_name`, `max_in_flight`,
`admission_timeout_seconds`, `dedup_ttl_seconds`, `dedup_max_entries`.

- Orchestrator **disabled by default** (`BERGAMA_ORCHESTRATOR__ENABLED=false`)
- Enabled mode requires an explicit `PublishPort` (or explicit `dry_run=true`)
- Dry-run is explicit and **never** reports `PUBLISHED`
- **Bounded in-flight admission control** — admission timeout → fail-closed `BUFFER_OVERFLOW`
- There is **no durable queue** and no background worker
- Dedup lifecycle: `reserve → publish → commit`; failure/dry-run → reservation release
- Dedup is **process-local**, TTL- and max-entry-bounded
- **Per-stream sequencing** on `(instrument_key, event_type)` — serializes same-stream work; **not** global/event-time sorting; timestamps are never repaired
- PIT events are never silently repaired; invalid PIT that cannot survive canonical construction surfaces as `REJECTED_VALIDATION`; `REJECTED_PIT` only when the PIT stage fails
- Append-only terminal audit + process-local metrics (no Prometheus)
- No Kafka / Iceberg / EventEnvelope adapter in #305 — a future Kafka adapter implements `PublishPort` without changing orchestration core

```bash
make test-api-market-orchestrator
```

## #304E scope

Shared offline contract suite across Polygon, Finnhub, FRED, SEC and Benzinga:

- identity / PIT / keys / Decimal / provenance / redaction
- retry taxonomy / pagination guards / container lifecycle
- EventEnvelope serialize/deserialize round-trip from provider-mapped events

### Contract philosophy

- Assert observable contracts, not private methods.
- Keep provider-specific semantics explicit (auth form, time policy, pagination model).
- Future providers should only need a fixture module + parametrization rows.

### Adding a new provider

See the **Provider Onboarding Guide**:  
[`docs/sprints/sprint-3/NEW_PROVIDER_CHECKLIST.md`](./NEW_PROVIDER_CHECKLIST.md)

Also summarized in [`apps/api/README.md`](../../../apps/api/README.md)
under **Provider Onboarding Guide**.

Extension process: settings → transport → schemas → mapper → fixtures →
contract matrix rows → focused tests → full provider gate.

**Certification:** `lint`, `typecheck`, `validate-secrets`, provider-focused
target, `test-api-provider-contracts`, and `test-api` must PASS. Live smoke may
be SKIPPED; offline contracts remain mandatory.

### Known intentional differences

- `source.provider` literal `sec_edgar` (not `sec`)
- Benzinga 403 → `entitlement_required`; others → `forbidden`
- Pagination error naming: FRED `pagination_state` vs Polygon/Benzinga `pagination_loop`
- Benzinga settings field `max_retry_after_seconds` vs others `retry_after_max_seconds`
- Finnhub fundamentals from one response share `source_event_id` (response observation identity)

## Commands

```bash
make lint
make typecheck
make validate-secrets
make test-api-market-contracts
make test-api-polygon-historical
make test-api-polygon-realtime
make test-api-finnhub-fundamentals
make test-api-fred-macro
make test-api-sec-filings
make test-api-benzinga-news
make test-api-provider-contracts
make test-api-market-orchestrator
make test-api
```

## Constraints

- No Kafka / Iceberg in #305.
- Orchestrator accepts `CanonicalMarketEvent` only.
- Connectors must not import the orchestrator.
- Do not commit secrets or real API keys.
