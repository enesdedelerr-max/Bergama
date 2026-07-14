# Sprint 3 — Market Data Plane

## Status

✅ **Sprint 2** complete on `main` (`v0.2.0-sprint2`, gate GO).  
✅ **Issue #301** Canonical Market Data Contract — complete on `main`.  
✅ **Issue #302** Polygon Historical Connector — stocks aggregate bars REST connector.  
⏳ **Issue #303** Polygon Realtime Connector — not started.

## Goal

Ingest provider market data into provider-independent, point-in-time-safe
canonical contracts. #302 maps Polygon stock historical aggregate bars into
#301 `BarEvent` models. Kafka publishing and Iceberg writes remain later issues.

## Issue chain (first slice)

1. ✅ **#301** Canonical Market Data Contract
2. ✅ **#302** Polygon Historical Connector
3. ⏳ **#303** Polygon Realtime Connector
4. Later: Finnhub / FRED / SEC EDGAR / Benzinga, Kafka publish, Iceberg, …

## #302 scope

- Package: `apps/api/app/infrastructure/polygon/`
- Endpoint: `GET /v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}`
- Auth: `Authorization: Bearer <api_key>` (SecretStr; never logged)
- Callers supply canonical `InstrumentId`, currency, and venue/context
- Daily bars: explicit policy `utc_fixed_24h_from_provider_t` (not exchange-session close);
  tracked as [TD-MARKET-DATA-001](../../tech-debt/TD-MARKET-DATA-001.md)
- Disabled by default (`BERGAMA_POLYGON__ENABLED=false`)
- No provider health check (no cheap honest probe without authenticated quota)
- No WebSocket, Kafka publish, Iceberg, persistence, backfill orchestration, or UI

## Commands

```bash
make lint
make typecheck
make validate-secrets
make test-api-market-contracts
make test-api-polygon-historical
make test-api
make smoke-api-polygon   # SKIPPED unless BERGAMA_POLYGON_SMOKE=1 + real API key
```

## Constraints

- No Kafka publishing / Iceberg writers in #302.
- No realtime WebSocket in #302 (#303).
- No trading / strategy / UI / #211 scope.
- Do not commit real Polygon API keys.
