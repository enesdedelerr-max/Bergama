# Sprint 3 — Market Data Plane

## Status

✅ **Sprint 2** complete on `main` (`v0.2.0-sprint2`, gate GO).  
✅ **Issue #301** Canonical Market Data Contract — complete on `main`.  
✅ **Issue #302** Polygon Historical Connector — complete on `main`.  
✅ **Issue #303** Polygon Realtime Connector — stocks WebSocket T/Q/AM transport.  
✅ **Issue #304A** Finnhub Fundamentals Connector — profile2 + basic financials whitelist.  
✅ **Issue #304B** FRED Macro Connector — series + observations → MacroEvent.  
✅ **Issue #304C** SEC EDGAR Filings Connector — submissions → FilingEvent.  
⏳ **Issue #304D** Benzinga News Connector — implemented on `feature/sprint3-issue304d-benzinga-news` (not yet merged).  
⏳ **Issue #304E** Cross-Provider Connector Contract Tests — not started.

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
8. ⏳ **#304E** Cross-Provider Connector Contract Tests
9. Later: Kafka publish, Iceberg, …

## #304D scope

- Package: `apps/api/app/infrastructure/benzinga/`
- Endpoint: `GET https://api.benzinga.com/api/v2/news`
- Header-only `Authorization: token …`; `displayOutput` headline|abstract only
- Map to `NewsEvent`; fan-out mapped tickers; caller `anchor_instrument` for others
- Revision identity via `source_event_id = {id}:{updated}`; no fabricated revision links
- No body mapping, scraping, channels catalog, news-removed, Kafka, Iceberg

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
make test-api
make smoke-api-polygon              # SKIPPED unless BERGAMA_POLYGON_SMOKE=1
make smoke-api-polygon-realtime     # SKIPPED unless BERGAMA_POLYGON_WS_SMOKE=1
make smoke-api-finnhub              # SKIPPED unless BERGAMA_FINNHUB_SMOKE=1
make smoke-api-fred                 # SKIPPED unless BERGAMA_FRED_SMOKE=1
make smoke-api-sec                  # SKIPPED unless BERGAMA_SEC_SMOKE=1
make smoke-api-benzinga             # SKIPPED unless BERGAMA_BENZINGA_SMOKE=1
```

## Constraints

- No Kafka publishing / Iceberg writers in #304D.
- No article body scraping / paywall bypass / sentiment / catalyst scoring.
- No trading / strategy / UI / #304E scope.
- Do not commit secrets or real API keys.
