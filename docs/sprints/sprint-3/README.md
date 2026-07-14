# Sprint 3 — Market Data Plane

## Status

✅ **Sprint 2** complete on `main` (`v0.2.0-sprint2`, gate GO).  
✅ **Issue #301** Canonical Market Data Contract — complete on `main`.  
✅ **Issue #302** Polygon Historical Connector — complete on `main`.  
✅ **Issue #303** Polygon Realtime Connector — stocks WebSocket T/Q/AM transport.  
✅ **Issue #304A** Finnhub Fundamentals Connector — profile2 + basic financials whitelist.  
✅ **Issue #304B** FRED Macro Connector — series + observations → MacroEvent.  
⏳ **Issue #304C** SEC EDGAR Filings Connector — not started.

## Goal

Ingest provider market data into provider-independent, point-in-time-safe
canonical contracts. #302/#303 map Polygon; #304A Finnhub reference/fundamentals;
#304B maps FRED/ALFRED observations into #301 MacroEvent. Kafka publishing and
Iceberg writes remain later issues.

## Issue chain (first slice)

1. ✅ **#301** Canonical Market Data Contract
2. ✅ **#302** Polygon Historical Connector
3. ✅ **#303** Polygon Realtime Connector
4. ✅ **#304A** Finnhub Fundamentals Connector
5. ✅ **#304B** FRED Macro Connector
6. ⏳ **#304C** SEC EDGAR Filings Connector
7. Later: Kafka publish, Iceberg, …

## #304B scope

- Package: `apps/api/app/infrastructure/fred/`
- Endpoints: `GET /fred/series`, `GET /fred/series/observations` (official API v1)
- Auth: query `api_key` (URL sanitized in logs; never in source metadata)
- Caller supplies InstrumentId + canonical series_id; FRED id in SourceReference
- Time: observation date UTC midnight → occurred/effective; realtime_start → known_at
- Missing `.` values skipped with warning; revisions distinct via source_event_id
- No frequency aggregation or unit transforms; no FRED health probe

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
make test-api
make smoke-api-polygon              # SKIPPED unless BERGAMA_POLYGON_SMOKE=1
make smoke-api-polygon-realtime     # SKIPPED unless BERGAMA_POLYGON_WS_SMOKE=1
make smoke-api-finnhub              # SKIPPED unless BERGAMA_FINNHUB_SMOKE=1
make smoke-api-fred                 # SKIPPED unless BERGAMA_FRED_SMOKE=1
```

## Constraints

- No Kafka publishing / Iceberg writers in #304B.
- No FRED search / categories / release calendar / bulk backfill in #304B.
- No trading / strategy / UI / #304C scope.
- Do not commit real API keys.
