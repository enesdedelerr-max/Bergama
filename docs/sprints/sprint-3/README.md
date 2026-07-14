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

`CanonicalMarketEvent → validate → PIT → quality → dedup reserve → ordering → route → bounded in-flight admission → PublishPort → dedup commit/release`

- Immutable `PipelineContext`
- Dedup reserve before publish; commit only after successful live delivery; release on failure/dry-run
- Ordering per `(instrument_key, event_type)` — no global sort
- Routing by canonical event type only (no Kafka topic names)
- **Bounded in-flight admission control** (`max_in_flight`, `admission_timeout_seconds`) — not a durable buffer or async queue
- Terminal delivery success is `PUBLISHED` (not `ACCEPTED`)
- Abstract `PublishPort` only — no Kafka / EventEnvelope / Iceberg in this issue
- Orchestrator disabled by default (`BERGAMA_ORCHESTRATOR__ENABLED=false`)
- Enabled mode requires an explicit `PublishPort` (or explicit `dry_run=true`)
- Dry-run never reports a successful live publish

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
