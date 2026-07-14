# Sprint 3 — Market Data Plane

## Status

✅ **Sprint 2** complete on `main` (`v0.2.0-sprint2`, gate GO).  
🟡 **Issue #301** Canonical Market Data Contract — in progress.

Do **not** implement provider connectors until #301 is merged.

## Goal

Ingest provider market data into provider-independent, point-in-time-safe
canonical contracts, then publish/store downstream. Connectors are later issues.

## Issue chain (first slice)

1. 🟡 **#301** Canonical Market Data Contract
2. ⏳ **#302** Polygon Historical Connector (blocked on #301)
3. Later: Finnhub / FRED / SEC EDGAR / Benzinga, Kafka publish, Iceberg, …

## #301 package

[`apps/api/app/market_data`](../../apps/api/app/market_data) — Decimal-native domain
models + JSON-safe EventEnvelope payload conversion. No connectors.

## Commands

```bash
make lint
make typecheck
make test-api-market-contracts
make test-api
```

## Constraints

- No provider SDKs or network connectors in #301.
- No Kafka publishing / Iceberg writers in #301.
- No trading / strategy / UI / #211 scope.
