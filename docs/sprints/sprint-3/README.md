# Sprint 3 — Market Data Plane

## Status

✅ **Sprint 2** complete on `main` (`v0.2.0-sprint2`, gate GO).  
✅ **Issue #301** Canonical Market Data Contract — complete on `main`.  
✅ **Issue #302** Polygon Historical Connector — complete on `main`.  
✅ **Issue #303** Polygon Realtime Connector — stocks WebSocket T/Q/AM transport.  
⏳ **Issue #304** External Data Connectors — not started.

## Goal

Ingest provider market data into provider-independent, point-in-time-safe
canonical contracts. #302/#303 map Polygon stocks into #301 events. Kafka
publishing and Iceberg writes remain later issues.

## Issue chain (first slice)

1. ✅ **#301** Canonical Market Data Contract
2. ✅ **#302** Polygon Historical Connector
3. ✅ **#303** Polygon Realtime Connector
4. ⏳ **#304** External Data Connectors
5. Later: Kafka publish, Iceberg, …

## #303 scope

- Package: `apps/api/app/infrastructure/polygon/` (`realtime.py`, `ws_*`)
- Endpoint: `wss://socket.polygon.io/stocks`
- Auth: `{"action":"auth","params":"<API_KEY>"}` (never logged)
- Channels: `T.<sym>`, `Q.<sym>`, `AM.<sym>` only (no `A`, options, crypto, forex, L2)
- Transport-only: connect → auth → subscribe → map → bounded queue
- Reconnect with full resubscribe; auth_failed terminal; overflow fail-closed
- Callers supply InstrumentId, currency, venue; ticker only in `SourceReference`
- Reconnect gaps are **not** filled in #303
- No Kafka / Iceberg / persistence / health probe claim

## Commands

```bash
make lint
make typecheck
make validate-secrets
make test-api-market-contracts
make test-api-polygon-historical
make test-api-polygon-realtime
make test-api
make smoke-api-polygon              # SKIPPED unless BERGAMA_POLYGON_SMOKE=1
make smoke-api-polygon-realtime     # SKIPPED unless BERGAMA_POLYGON_WS_SMOKE=1
```

## Constraints

- No Kafka publishing / Iceberg writers in #303.
- No gap-fill / backfill orchestration in #303.
- No trading / strategy / UI / #211 scope.
- Do not commit real Polygon API keys.
