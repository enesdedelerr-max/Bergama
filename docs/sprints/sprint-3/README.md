# Sprint 3 — Market Data Plane

## Status

✅ **Sprint 2** complete on `main` (`v0.2.0-sprint2`, gate GO).  
✅ **Issue #301** Canonical Market Data Contract — complete on `main`.  
✅ **Issue #302** Polygon Historical Connector — complete on `main`.  
✅ **Issue #303** Polygon Realtime Connector — stocks WebSocket T/Q/AM transport.  
✅ **Issue #304A** Finnhub Fundamentals Connector — profile2 + basic financials whitelist.  
⏳ **Issue #304B** FRED Macro Connector — not started.

## Goal

Ingest provider market data into provider-independent, point-in-time-safe
canonical contracts. #302/#303 map Polygon stocks into #301 events; #304A maps
Finnhub profile/metrics into #301 reference/fundamental events. Kafka
publishing and Iceberg writes remain later issues.

## Issue chain (first slice)

1. ✅ **#301** Canonical Market Data Contract
2. ✅ **#302** Polygon Historical Connector
3. ✅ **#303** Polygon Realtime Connector
4. ✅ **#304A** Finnhub Fundamentals Connector
5. ⏳ **#304B** FRED Macro Connector
6. Later: Kafka publish, Iceberg, …

## #304A scope

- Package: `apps/api/app/infrastructure/finnhub/`
- Endpoints: `GET /stock/profile2`, `GET /stock/metric?metric=all`
- Auth: `X-Finnhub-Token` only (never query `token`)
- Closed `SUPPORTED_METRICS` with explicit period/unit tables; unknown metrics ignored
- Profile: canonical `name` only from Finnhub; other Finnhub fields in bounded `attributes`
- Timestamps: connector observation clock (one `observed_at` per response)
- Request ID provenance: `source.extras.http_request_id` (see `docs/tech-debt/TD-MARKET-DATA-002.md`)
- No Finnhub health probe; no Kafka / Iceberg / series / news / earnings / WS

## Commands

```bash
make lint
make typecheck
make validate-secrets
make test-api-market-contracts
make test-api-polygon-historical
make test-api-polygon-realtime
make test-api-finnhub-fundamentals
make test-api
make smoke-api-polygon              # SKIPPED unless BERGAMA_POLYGON_SMOKE=1
make smoke-api-polygon-realtime     # SKIPPED unless BERGAMA_POLYGON_WS_SMOKE=1
make smoke-api-finnhub              # SKIPPED unless BERGAMA_FINNHUB_SMOKE=1
```

## Constraints

- No Kafka publishing / Iceberg writers in #304A.
- No series mapping / news / earnings / recommendations / WebSocket in #304A.
- No trading / strategy / UI / #304B scope.
- Do not commit real Finnhub or Polygon API keys.
