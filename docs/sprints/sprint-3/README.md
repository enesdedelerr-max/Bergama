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
✅ **Issue #307** Iceberg Writer — complete on `main` (PR #34).  
⏳ **Issue #308** Replay Engine — in progress on feature branch.

## Goal

Ingest provider market data into provider-independent, point-in-time-safe
canonical contracts, publish EventEnvelope records to Kafka, append into Iceberg,
and deterministically replay persisted events without calling providers.

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
11. ✅ **#307** Iceberg Writer
12. ⏳ **#308** Replay Engine
13. Later: Historical Backfill Pipeline (#309), …

## #308 scope

`ReplayRequest → IcebergReplaySource → reconstruct → order → isolated MarketDataOrchestrator → explicit sink or none → audit → checkpoint`

- Primary source: eight Iceberg market-data tables (no Kafka consumer-group rewind)
- Default mode `dry_run`; side-effect modes require an explicit injected sink
- Deterministic order `(occurred_at, event_type, instrument_key, idempotency_key)`
- Preserve original PIT timestamps and `idempotency_key` (at-least-once republish)
- Lossy reconstruction when lake columns omit fields; synthetic `symbol_effective_from` when missing
- Atomic file checkpoint/resume; request fingerprint must match
- Disabled by default; no startup replay; no replay readiness health

```bash
make test-api-replay-engine
make smoke-api-replay-engine
```

Optional local smoke: `BERGAMA_REPLAY_ENGINE_SMOKE=1` (local Iceberg tables, dry-run).

## #307 scope

`Kafka market-data → EventConsumer → EventEnvelope → canonical reconstruction → Iceberg append → snapshot → Kafka offset`

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
make test-api-replay-engine
make test-api
make smoke-api-kafka-publish
make smoke-api-iceberg-writer
make smoke-api-replay-engine
```

## Constraints

- Replay never calls provider connectors or mutates Kafka offsets.
- Replay never silently selects the production Kafka publish adapter.
- No Iceberg rewrite sink in #308.
- Do not claim exactly-once.
- Do not implement #309 in this issue.
- Do not commit secrets or real API keys.
