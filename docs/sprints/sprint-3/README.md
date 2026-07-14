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
✅ **Issue #305** Market Data Orchestrator — complete on `main` (PR #32).  
✅ **Issue #306** Kafka Publish Adapter — complete on `main` (PR #33).  
⏳ **Issue #307** Iceberg Writer — in progress on feature branch.

## Goal

Ingest provider market data into provider-independent, point-in-time-safe
canonical contracts, publish EventEnvelope records to Kafka, and append into Iceberg.

## Issue chain (first slice)

1. ✅ **#301** Canonical Market Data Contract
2. ✅ **#302** Polygon Historical Connector
3. ✅ **#303** Polygon Realtime Connector
4. ✅ **#304A** Finnhub Fundamentals Connector
5. ✅ **#304B** FRED Macro Connector
6. ✅ **#304C** SEC EDGAR Filings Connector
7. ✅ **#304D** Benzinga News Connector
8. ✅ **#304E** Cross-Provider Connector Contract Tests
9. ✅ **#305** Market Data Orchestrator
10. ✅ **#306** Kafka Publish Adapter
11. ⏳ **#307** Iceberg Writer
12. Later: Replay Engine (#308), …

## #307 scope

`Kafka market-data → EventConsumer → EventEnvelope → canonical reconstruction → Iceberg append → snapshot → Kafka offset`

- Append-only Iceberg snapshots (`pyiceberg[pyarrow,sql-sqlite]==0.11.1`)
- Explicit table routing by canonical event type (eight tables)
- Partition: `day(occurred_at)` — Decimal policy `decimal(38,18)`
- Bounded micro-batch flush; multi-table snapshots in stable table-name order
- Kafka offsets only after every affected table snapshot succeeds
- Process-local committed-key index (TTL + max entries) — not durable across restart
- At-least-once Kafka; no exactly-once / upsert / merge-on-read claims
- Multi-table Iceberg commits are not one atomic transaction
- Ordering preserved only within a Kafka partition
- Disabled by default; auto-create tables local/test only
- Shutdown: stop intake → flush → snapshots → offsets → writer consumer → catalog → Kafka runtime → providers

```bash
make test-api-iceberg-writer
make smoke-api-iceberg-writer
```

Optional live smoke: `BERGAMA_ICEBERG_WRITER_SMOKE=1` with Kafka, REST catalog, MinIO,
pre-created `market-data` topic and tables (or explicit local `auto_create_tables`).

## #306 scope

`CanonicalMarketEvent → MarketDataOrchestrator → PublishPort → KafkaPublishAdapter → market_event_to_envelope → EventProducer → Kafka (market-data)`

## Commands

```bash
make lint
make typecheck
make validate-secrets
make test-api-market-contracts
make test-api-provider-contracts
make test-api-market-orchestrator
make test-api-kafka-core
make test-api-kafka-test-runtime
make test-api-kafka-publish-adapter
make test-api-iceberg-writer
make test-api
make smoke-api-kafka-publish
make smoke-api-iceberg-writer
```

## Constraints

- Writer consumes EventEnvelope only — no connector/orchestrator coupling.
- No Kafka produce from the writer.
- No upsert / merge-on-read / equality deletes in #307.
- Do not claim exactly-once.
- Do not commit secrets or real API keys.
