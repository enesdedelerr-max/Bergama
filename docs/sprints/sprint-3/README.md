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
⏳ **Issue #306** Kafka Publish Adapter — in progress on feature branch.

## Goal

Ingest provider market data into provider-independent, point-in-time-safe
canonical contracts. Iceberg writes remain a later issue.

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
10. ⏳ **#306** Kafka Publish Adapter
11. Later: Iceberg writer, …

## #306 scope

`CanonicalMarketEvent → MarketDataOrchestrator → PublishPort → KafkaPublishAdapter → market_event_to_envelope → EventProducer → Kafka (market-data)`

- Orchestrator core remains Kafka-free and EventEnvelope-free
- All approved `market.*` routing keys map to `KafkaTopic.MARKET_DATA`
- Deterministic Kafka record key = canonical idempotency key
- At-least-once acknowledgement semantics (not exactly-once)
- `publish_backend=kafka` is explicit; enabling Kafka alone does not select the adapter
- Fail-closed when kafka mode lacks a producer
- Shutdown: orchestrator → Kafka runtime → provider clients
- Offline in-memory broker tests; optional live smoke via `BERGAMA_KAFKA_PUBLISH_SMOKE=1`

```bash
make test-api-kafka-publish-adapter
make smoke-api-kafka-publish
```

## #305 scope

Canonical-event pipeline after connectors:

`CanonicalMarketEvent → validate → PIT → quality → per-stream acquire → dedup reserve → route → bounded in-flight admission → PublishPort → dedup commit/release → stream release`

Settings: `enabled`, `dry_run`, `publish_backend`, `pipeline_name`, `max_in_flight`,
`admission_timeout_seconds`, `dedup_ttl_seconds`, `dedup_max_entries`.

```bash
make test-api-market-orchestrator
```

## #304E scope

Shared offline contract suite across Polygon, Finnhub, FRED, SEC and Benzinga.

See the **Provider Onboarding Guide**:  
[`docs/sprints/sprint-3/NEW_PROVIDER_CHECKLIST.md`](./NEW_PROVIDER_CHECKLIST.md)

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
make test-api
make smoke-api-kafka-publish
```

## Constraints

- Orchestrator accepts `CanonicalMarketEvent` only.
- No Kafka imports inside the orchestrator package.
- No Iceberg / consumer / DLQ in #306.
- Do not commit secrets or real API keys.
