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
✅ **Issue #308** Replay Engine — complete on `main`.  
✅ **Issue #309** Historical Backfill Pipeline — complete on `main` (PR #36).  
⏳ **Issue #310** Data Quality and Monitoring — in progress on feature branch.

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
12. ✅ **#308** Replay Engine
13. ✅ **#309** Historical Backfill Pipeline
14. ⏳ **#310** Data Quality and Monitoring
15. Later: Sprint 3 Runtime Gate and Release (#311), …

## #310 scope

`CanonicalMarketEvent → canonical/PIT validation → DataQualityService.evaluate() → QualityAssessment → orchestrator decision → audit/metrics → QualitySnapshot → AlertSignal`

- New subsystem under `app.market_data.data_quality`; existing `app.market_data.quality.DataQualityFlags` remains the canonical flag contract.
- Disabled by default; enabled mode is observe-only by default.
- Enforcement requires explicit policy configuration; observe-only never rejects, quarantines or halts.
- Closed rule taxonomy, immutable `QualityAssessment`, deterministic policy fingerprinting.
- Process-local bounded metrics and deterministic snapshots; no Prometheus exporter in #310.
- Alert-ready typed signals only; no PagerDuty/Slack/email delivery.
- Quarantine protocol plus local/test implementations only; no Kafka quarantine topic or Iceberg quarantine table.
- Narrow orchestrator integration with explicit `QUALITY_REJECTED`, `QUALITY_QUARANTINED`, and `QUALITY_HALT` decisions.
- No provider calls, data repair, timestamp repair, missing-value imputation, ML anomaly detection or #311.

```bash
make test-api-data-quality
make smoke-api-data-quality
```

## #309 scope

`BackfillRequest → BackfillSource → slices → existing connector → CanonicalMarketEvent → isolated MarketDataOrchestrator → explicit PublishPort or none → checkpoint → audit`

- Historical: Polygon aggregates, FRED observations, Benzinga bounded news
- Bounded refresh: Finnhub profile/fundamentals, SEC filings.recent
- Unsupported: Polygon realtime, SEC archives
- Default mode `dry_run`; publish requires explicit injected sink
- Deterministic provider-specific slices; `may_have_more` fails closed
- Dedicated atomic file checkpoint (not ReplayCheckpoint)
- Preserve connector idempotency keys; at-least-once only
- Disabled by default; no startup run; no backfill readiness health

```bash
make test-api-backfill
make smoke-api-backfill
```

Optional live smoke: `BERGAMA_BACKFILL_SMOKE=1` with `BERGAMA_BACKFILL_SMOKE_PROVIDER=polygon` (exactly one provider; tiny dry_run).

## #308 scope

`ReplayRequest → IcebergReplaySource → reconstruct → order → isolated MarketDataOrchestrator → explicit sink or none → audit → checkpoint`

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
make test-api-backfill
make test-api-data-quality
make test-api
make smoke-api-kafka-publish
make smoke-api-iceberg-writer
make smoke-api-replay-engine
make smoke-api-backfill
make smoke-api-data-quality
```

## Constraints

- Backfill never uses raw httpx in core; adapters wrap existing connectors.
- Backfill never writes Kafka/Iceberg directly or reuses ReplayCheckpoint.
- Backfill never silently selects the production Kafka publish adapter.
- Data quality never calls providers, repairs data, publishes directly, writes Iceberg directly or sends external alerts.
- Do not claim exactly-once.
- Do not implement #311 in #310.
- Do not commit secrets or real API keys.
