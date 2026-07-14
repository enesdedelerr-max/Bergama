# Sprint 3 — Market Data Plane

## Status

✅ **Sprint 2** complete on `main` (`v0.2.0-sprint2`, gate GO).  
✅ **Issue #301** Canonical Market Data Contract — complete on `main`.  
✅ **Issue #302** Polygon Historical Connector — complete on `main`.  
✅ **Issue #303** Polygon Realtime Connector — stocks WebSocket T/Q/AM transport.  
✅ **Issue #304A** Finnhub Fundamentals Connector — profile2 + basic financials whitelist.  
✅ **Issue #304B** FRED Macro Connector — series + observations → MacroEvent.  
✅ **Issue #304C** SEC EDGAR Filings Connector — submissions → FilingEvent.  
⏳ **Issue #304D** Benzinga News Connector — not started.

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
7. ⏳ **#304D** Benzinga News Connector
8. Later: Kafka publish, Iceberg, …

## #304C scope

- Package: `apps/api/app/infrastructure/sec/`
- Endpoint: `GET https://data.sec.gov/submissions/CIK##########.json`
- Required descriptive User-Agent with contact; conservative rate limiter
- Map `filings.recent` only; preserve `filings.files` refs without fetching
- Accession identity; amendments remain distinct; no ticker→CIK inference
- No document download / XBRL parsing / Kafka / Iceberg

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
make test-api
make smoke-api-polygon              # SKIPPED unless BERGAMA_POLYGON_SMOKE=1
make smoke-api-polygon-realtime     # SKIPPED unless BERGAMA_POLYGON_WS_SMOKE=1
make smoke-api-finnhub              # SKIPPED unless BERGAMA_FINNHUB_SMOKE=1
make smoke-api-fred                 # SKIPPED unless BERGAMA_FRED_SMOKE=1
make smoke-api-sec                  # SKIPPED unless BERGAMA_SEC_SMOKE=1
```

## Constraints

- No Kafka publishing / Iceberg writers in #304C.
- No filing-body download / XBRL fact extraction / archive backfill in #304C.
- No trading / strategy / UI / #304D scope.
- Do not commit secrets or real production contact emails unless intentionally local-only.
