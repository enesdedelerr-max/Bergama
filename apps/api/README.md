# Bergama API — Sprint 2 Runtime Foundation

FastAPI runtime for the AI Hedge Fund Operating System.

## Issue status

- ✅ **#201** Runtime Bootstrap
- ✅ **#202** Configuration Layer
- ✅ **#203** Structured Logging
- ✅ **#204** Secret Handling
- ✅ **#205** JWT Bootstrap
- ✅ **#206** Dependency Injection Container
- ✅ **#207** Health Runtime
- ✅ **#208A** Kafka Core Runtime
- ✅ **#208B** Kafka Test Runtime
- ✅ **#209** Registry Loader
- ✅ **#210** Runtime Smoke Tests and Sprint 2 Gate
- Out of gate: #211 Trading Engine Foundation (excluded)
- ✅ **#301** Canonical Market Data Contract (Sprint 3)
- ✅ **#302** Polygon Historical Connector (Sprint 3)
- ✅ **#303** Polygon Realtime Connector (Sprint 3)
- ⏳ **#304** External Data Connectors (not started)

## Canonical market data (#301)

Provider-independent PIT-safe contracts under `app/market_data/`.

| Item | Behavior |
|------|----------|
| Identity | `InstrumentId.instrument_key` is canonical; provider symbols stay on `SourceReference` |
| Time | Payload carries `occurred_at`, `effective_at`, `known_at`, `ingested_at` (UTC) |
| Envelope map | `EventEnvelope.occurred_at` ← event `occurred_at`; `ingested_at` ← event `ingested_at` |
| Money | Decimal-native models; transport uses canonical Decimal strings |
| Events | quote, trade, bar, reference_data, fundamental, macro, filing, news |
| Keys | Deterministic idempotency + deduplication builders |
| Out of scope | Provider connectors (#302+), Kafka publish, Iceberg, features/strategies |

```bash
make test-api-market-contracts
```

## Polygon historical connector (#302)

Stocks custom aggregate bars only (`/v2/aggs/ticker/.../range/...`). Maps to canonical `BarEvent`.

| Item | Behavior |
|------|----------|
| Default | `BERGAMA_POLYGON__ENABLED=false` (no HTTP client constructed) |
| Auth | `Authorization: Bearer` via `BERGAMA_POLYGON__API_KEY` (`SecretStr`) |
| Identity | Caller supplies `InstrumentId` + ISO currency; Polygon ticker → `SourceReference.source_symbol` only |
| Windows | Minute/hour: exact duration; day: `utc_fixed_24h_from_provider_t` (not NYSE RTH close) |
| Pagination | Follow `next_url` only; same https host; loop + max-page guards |
| Retry | Connect/timeout/429/5xx only; bounded backoff; injectable sleeper |
| Health | Omitted — no cheap honest Polygon probe without quota burn |
| Live smoke | `make smoke-api-polygon` — SKIPPED unless `BERGAMA_POLYGON_SMOKE=1` |
| Out of scope | WebSocket (#303), Kafka publish, Iceberg, backfill orchestration, other providers |

```bash
make test-api-polygon-historical
make smoke-api-polygon
```

## Polygon realtime connector (#303)

Stocks WebSocket only (`T` / `Q` / `AM`). Transport-only — no Kafka publish.

| Item | Behavior |
|------|----------|
| Default | `BERGAMA_POLYGON__WEBSOCKET_ENABLED=false` (requires `ENABLED=true`) |
| Auth | `{"action":"auth","params":...}` after connect; never logged |
| Channels | Explicit `T./Q./AM.` only; full resubscribe after reconnect |
| Queue | Bounded; overflow fails closed (disconnect, no silent drop) |
| Identity | Caller supplies InstrumentId, currency, venue; `sym` → SourceReference only |
| Gaps | Reconnect gaps are not filled in #303 |
| Live smoke | `make smoke-api-polygon-realtime` — SKIPPED unless `BERGAMA_POLYGON_WS_SMOKE=1` |
| Out of scope | Kafka publish, Iceberg, gap-fill, second aggregates (`A`), other asset classes |

```bash
make test-api-polygon-realtime
make smoke-api-polygon-realtime
```

## Finnhub fundamentals connector (#304A)

Company Profile 2 (`/stock/profile2`) → `ReferenceDataEvent` and Basic Financials
(`/stock/metric?metric=all`) → `FundamentalEvent` via a closed Finnhub metric whitelist.

| Item | Behavior |
|------|----------|
| Default | `BERGAMA_FINNHUB__ENABLED=false` (no HTTP client constructed) |
| Auth | `X-Finnhub-Token` header only (`BERGAMA_FINNHUB__API_KEY` as `SecretStr`; never query `token`) |
| Identity | Caller supplies `InstrumentId`; Finnhub ticker stays in `SourceReference` |
| Profile attributes | Provider fields in bounded `attributes` only; no ISIN/CUSIP/MIC/sector invention |
| Metrics | Explicit `SUPPORTED_METRICS` + period/unit tables; unknown keys ignored (DEBUG key only) |
| Timestamps | One `observed_at = clock.now()` per response → all PIT fields (connector observation, not publication) |
| Retry | Connect/timeout/429/5xx; bounded backoff; capped Retry-After; injectable sleeper |
| Health | Omitted — no cheap honest Finnhub probe without authenticated quota |
| Provenance | Provider HTTP request ID → `source.extras.http_request_id` (TD-MARKET-DATA-002) |
| Live smoke | `make smoke-api-finnhub` — SKIPPED unless `BERGAMA_FINNHUB_SMOKE=1` |
| Out of scope | Series mapping, news, earnings, WS, Kafka, Iceberg, cache, backfill, #304B |

```bash
make test-api-finnhub-fundamentals
make smoke-api-finnhub
```

## FRED macro connector (#304B)

Series metadata (`/fred/series`) and observations (`/fred/series/observations`) map to
canonical `MacroEvent` with ALFRED realtime vintage identity preserved.

| Item | Behavior |
|------|----------|
| Default | `BERGAMA_FRED__ENABLED=false` (no HTTP client constructed) |
| Auth | Query `api_key` per official FRED docs (`SecretStr`); URLs sanitized before logging |
| Identity | Caller supplies `InstrumentId` + canonical `series_id`; FRED id → `SourceReference` |
| Time | `effective_at`/`occurred_at` = observation date UTC midnight; `known_at` = `realtime_start` UTC midnight; `ingested_at` = clock per page |
| Missing `.` | Skipped with WARNING + result counter; never coerced to zero |
| Units | FRED unit strings in metadata only — no invented percentages/currency |
| Frequency | Explicit map to daily/weekly/monthly/quarterly/annual; unknown kept raw in metadata |
| Health | Omitted — no cheap honest FRED probe without authenticated quota |
| Live smoke | `make smoke-api-fred` — SKIPPED unless `BERGAMA_FRED_SMOKE=1` |
| Out of scope | Search, categories, aggregation transforms, Kafka, Iceberg, #304C |

```bash
make test-api-fred-macro
make smoke-api-fred
```

## SEC EDGAR filings connector (#304C)

Company submissions (`GET /submissions/CIK##########.json`) map `filings.recent` rows to
canonical `FilingEvent`. Archive file refs are preserved as metadata only.

| Item | Behavior |
|------|----------|
| Default | `BERGAMA_SEC__ENABLED=false` (no HTTP client constructed) |
| Auth | No API key — descriptive SEC User-Agent with contact email required when enabled |
| Identity | Caller supplies `InstrumentId` + CIK; CIK only in `SourceReference` |
| Accession | Preserved with dashes; dashless form used only for archive URL paths |
| Time | `effective_at` = filingDate UTC midnight; `known_at`/`occurred_at` = acceptanceDateTime when present |
| Rate limit | Conservative min-interval limiter (default 0.2s); official ceiling is 10 req/s |
| Health | Omitted — submissions are filing-data payloads, not a cheap probe |
| Live smoke | `make smoke-api-sec` — SKIPPED unless `BERGAMA_SEC_SMOKE=1` |
| Out of scope | Document download, XBRL fact parse, archive backfill, Kafka, Iceberg, #304D |

```bash
make test-api-sec-filings
make smoke-api-sec
```

## Benzinga news connector (#304D)

Newsfeed REST (`GET /api/v2/news`) maps stories to canonical `NewsEvent` with optional
caller ticker→instrument mapping and revision-aware source keys.

| Item | Behavior |
|------|----------|
| Default | `BERGAMA_BENZINGA__ENABLED=false` (no HTTP client constructed) |
| Auth | Header `Authorization: token <key>` only (`SecretStr`); query `token` never used |
| Content | `displayOutput=abstract` default; `headline` allowed; `full` rejected; body never mapped |
| Identity | Story `id` + `updated` → `source_event_id`; no fabricated `revision_of_event_id` |
| Instruments | Fan-out per mapped ticker; unmapped/zero-ticker requires caller `anchor_instrument` |
| Bounds | Require `date` / `dateFrom+dateTo` / `updatedSince` / `publishedSince` + max pages |
| Health | Omitted — no cheap honest Newsfeed probe without entitled quota |
| Live smoke | `make smoke-api-benzinga` — SKIPPED unless `BERGAMA_BENZINGA_SMOKE=1` |
| Out of scope | Channels catalog, news-removed, WebSocket, scraping, Kafka, Iceberg, #304E |

```bash
make test-api-benzinga-news
make smoke-api-benzinga
```

## Cross-provider connector contracts (#304E)

Offline quality gate proving Polygon, Finnhub, FRED, SEC and Benzinga adapters obey
shared identity, PIT, key, Decimal, provenance, redaction, retry, pagination,
lifecycle and EventEnvelope rules.

| Item | Behavior |
|------|----------|
| Target | `make test-api-provider-contracts` (offline, no credentials) |
| Fixtures | `tests/support/provider_contracts/` — synthetic only |
| Assertions | Provider-agnostic helpers in `assertions.py` |
| Included in | `make test-api` via `tests/contract/` discovery |
| Out of scope | New connectors in #304E itself, Kafka, Iceberg, orchestration, #305 |

```bash
make test-api-provider-contracts
```

## Provider Onboarding Guide

Full checklist: [`docs/sprints/sprint-3/NEW_PROVIDER_CHECKLIST.md`](../../docs/sprints/sprint-3/NEW_PROVIDER_CHECKLIST.md)

Every new provider must include typed settings, explicit auth boundary, `SecretStr`
credentials, async HTTP/WS transport, bounded retry, explicit pagination/streaming,
provider schemas, canonical mapper, `SourceReference`, deterministic idempotency/
dedup keys, container-owned lifecycle, offline fixtures, contract matrix entry,
provider-focused tests, and optional live smoke.

**Certification** (all required; live smoke may be SKIPPED):

```bash
make lint
make typecheck
make validate-secrets
# make test-api-<provider-focused-target>
make test-api-provider-contracts
make test-api
```

Offline contract validation is mandatory. Live smoke never substitutes for it.
Shared-runtime changes beyond provider-local modules require an explicit PR rationale.
Do not add orchestration, Kafka, Iceberg, provider fallback, or #305 in a provider PR.

## Market Data Orchestrator (#305)

Provider-independent pipeline after connectors have produced `CanonicalMarketEvent`.

| Setting | Default | Notes |
|---------|---------|-------|
| `BERGAMA_ORCHESTRATOR__ENABLED` | `false` | No active orchestrator when disabled |
| `BERGAMA_ORCHESTRATOR__DRY_RUN` | `false` | Requires enabled; never reports `PUBLISHED` |
| `BERGAMA_ORCHESTRATOR__PUBLISH_BACKEND` | `none` | `none` or `kafka` (#306); Kafka alone never auto-selects |
| `BERGAMA_ORCHESTRATOR__PIPELINE_NAME` | `market-data-orchestrator` | Audit / metrics identity |
| `BERGAMA_ORCHESTRATOR__MAX_IN_FLIGHT` | `64` | Bounded in-flight admission control |
| `BERGAMA_ORCHESTRATOR__ADMISSION_TIMEOUT_SECONDS` | `0.05` | Timeout → `BUFFER_OVERFLOW` |
| `BERGAMA_ORCHESTRATOR__DEDUP_TTL_SECONDS` | `3600` | Process-local committed TTL |
| `BERGAMA_ORCHESTRATOR__DEDUP_MAX_ENTRIES` | `50000` | Bounded store with deterministic eviction |

Rules:

- Enabled + `publish_backend=none` requires an explicit `PublishPort` injection (fail-closed otherwise).
- Enabled + `publish_backend=kafka` requires Kafka enabled with a producer (`KafkaPublishAdapter`).
- Dry-run is explicit and cannot combine with `publish_backend=kafka`.
- There is **no durable queue** — only bounded in-flight admission control.
- Dedup: `reserve → publish → commit`; failure/dry-run releases the reservation. Dedup is process-local and TTL/max-entry bounded.
- Per-stream sequencing `(instrument_key, event_type)` serializes same-stream work; it is **not** global or event-time ordering.
- PIT timestamps are never repaired. Canonical model construction may reject invalid PIT before the PIT stage (`REJECTED_VALIDATION`); `REJECTED_PIT` is only when the PIT stage itself fails.
- Terminal outcomes emit exactly one append-only audit record and process-local metrics (no Prometheus; no payload/secret labels).
- Shutdown order: orchestrator → Kafka runtime → provider clients.
- No Iceberg in #305/#306. Kafka consumer / DLQ remain out of scope for #306.

```bash
make test-api-market-orchestrator
```

## Kafka Publish Adapter (#306)

Infrastructure `PublishPort` implementation: `KafkaPublishAdapter`.

Flow:

`CanonicalMarketEvent → orchestrator → PublishPort → KafkaPublishAdapter → market_event_to_envelope → EventProducer → Kafka topic market-data`

| Concern | Policy |
|---------|--------|
| Topic | All approved `market.*` routing keys → `KafkaTopic.MARKET_DATA` |
| Record key | Canonical `idempotency_key` (deterministic; never random UUID) |
| Delivery | At-least-once broker acknowledgement |
| `idempotency_acknowledged` | Broker accepted the record with that key — not exactly-once |
| Metadata | `topic` / `partition` / `offset` only in `PublishResult.safe_metadata` |
| Retries | No orchestrator/adapter retry layer; fail closed and release dedup reservation |

```bash
make test-api-kafka-publish-adapter
make smoke-api-kafka-publish   # SKIPPED unless BERGAMA_KAFKA_PUBLISH_SMOKE=1
```

## Iceberg Writer (#307)

Append-only Kafka → Iceberg sink for canonical market-data envelopes.

Flow:

`Kafka market-data → EventConsumer → EventEnvelope → canonical event → Iceberg append → snapshot → Kafka offset`

| Concern | Policy |
|---------|--------|
| Client | `pyiceberg[pyarrow,sql-sqlite]==0.11.1` (no Spark/Flink) |
| Tables | Eight tables by event family (`market_quotes`, …); unknown type fail-closed |
| Partition | `day(occurred_at)` only |
| Decimal | Fixed `decimal(38,18)` — no float coercion |
| Delivery | At-least-once Kafka; append-only Iceberg |
| Dedup | Process-local committed-key index (TTL + max entries); duplicates may reappear after restart |
| Multi-table | Snapshots in stable table-name order; **not** one atomic transaction across tables |
| Offsets | Committed only after every affected table snapshot succeeds |
| Ordering | Within Kafka partition only |
| Defaults | Writer disabled; `auto_create_tables=false` (local/test only when true) |
| Shutdown | intake stop → flush → snapshots → offsets → writer consumer → catalog → Kafka runtime → providers |

No upsert, merge-on-read, equality deletes, or exactly-once claims.

```bash
make test-api-iceberg-writer
make smoke-api-iceberg-writer   # SKIPPED unless BERGAMA_ICEBERG_WRITER_SMOKE=1
```

## Replay Engine (#308)

Deterministic replay of persisted Iceberg canonical market-data rows.

Flow:

`ReplayRequest → IcebergReplaySource → reconstruct → order → isolated MarketDataOrchestrator → explicit sink or none → audit → checkpoint`

| Concern | Policy |
|--------|--------|
| Source | Iceberg eight tables only (no Kafka rewind, no arbitrary SQL/paths) |
| Default mode | `dry_run` — no sink, never reports published |
| Modes | `dry_run`, `validate_only`, `republish`, `custom_sink` |
| Side effects | Require explicit per-run sink; never auto-select production Kafka adapter |
| Ordering | `(occurred_at, event_type, instrument_key, idempotency_key)` — replay order, not Kafka order |
| Identity | Preserve original `idempotency_key` and PIT timestamps; at-least-once republish only |
| Reconstruction | Lossy for unstored fields; synthetic `symbol_effective_from` from `effective_at`/`occurred_at` when missing |
| Checkpoint | Atomic file JSON; resume after last successful cursor; fingerprint must match |
| Lifecycle | Disabled by default; construct only when enabled; explicit `run()` only |

```bash
make test-api-replay-engine
make smoke-api-replay-engine   # SKIPPED unless BERGAMA_REPLAY_ENGINE_SMOKE=1
```

## Historical Backfill Pipeline (#309)

Bounded, resumable provider backfill into canonical market-data events.

Flow:

`BackfillRequest → BackfillSource → slices → existing connector → CanonicalMarketEvent → isolated MarketDataOrchestrator → explicit PublishPort or none → checkpoint → audit`

| Concern | Policy |
|--------|--------|
| Capability | Polygon/FRED/Benzinga historical; Finnhub/SEC bounded refresh; realtime/archives unsupported |
| Default mode | `dry_run` — fetch/map/validate, no sink, never reports published |
| Modes | `dry_run`, `validate_only`, `publish` (explicit `PublishPort` only) |
| Request | One provider + one `source_kind`; typed selectors; no credentials/URLs/paths |
| Slicing | Provider-specific deterministic slices; `may_have_more` fails closed |
| Ordering | `(slice_start, occurred_at, event_type, instrument_key, idempotency_key)` |
| Identity | Preserve connector `idempotency_key`; at-least-once publish only |
| Checkpoint | Dedicated atomic file JSON (not ReplayCheckpoint); fingerprint must match |
| Lifecycle | Disabled by default; construct when enabled; explicit `run()` only; no backfill health |

```bash
make test-api-backfill
make smoke-api-backfill   # SKIPPED unless BERGAMA_BACKFILL_SMOKE=1 (+ provider)
```

## Data Quality and Monitoring (#310)

Deterministic, provider-independent quality assessment for canonical market-data flows.

Flow:

`CanonicalMarketEvent → canonical/PIT validation → DataQualityService.evaluate() → QualityAssessment → orchestrator quality decision → audit/metrics → QualitySnapshot → AlertSignal`

| Concern | Policy |
|--------|--------|
| Default | Disabled. When enabled, `observe_only=true` by default |
| Enforcement | Requires explicit policy settings; observe-only never rejects/quarantines/halts |
| Contracts | Existing `DataQualityFlags` in `app.market_data.quality` remain unchanged |
| Package | New subsystem lives under `app.market_data.data_quality` |
| Rules | Closed rule IDs only; no free-form runtime rule names |
| Policy | Optional local YAML/JSON only; duplicate-key-safe, size-bounded, no remote URLs |
| Metrics | Process-local bounded counters/snapshots; no Prometheus exporter in #310 |
| Alerts | Typed `AlertSignal` models only; no external notification delivery |
| Quarantine | Protocol plus local/test in-memory/file implementations; no Kafka topic/Iceberg table |
| Orchestrator | Quality reject/quarantine/halt never calls `PublishPort` |

Continuity gap detection is deferred until an explicit cadence/calendar policy exists.

```bash
make test-api-data-quality
make smoke-api-data-quality
```

## Sprint 2 gate (#210)

Fail-closed verification of the FastAPI Runtime Foundation:

```bash
make gate-sprint2
```

| Item | Behavior |
|------|----------|
| Required | lint, typecheck, secrets, all API/auth/container/health/Kafka/registry tests, OpenAPI, runtime smoke, release package |
| Optional | `make smoke-api-kafka` — SKIPPED unless `BERGAMA_KAFKA_SMOKE=1` |
| Live Kafka SKIPPED | Does **not** fail the gate |
| Live Kafka FAIL | Fails the gate when explicitly enabled |
| Evidence | `artifacts/sprint2/` |
| Report | `reports/sprint2-runtime-validation.json` |
| Release | `releases/sprint-2/` |
| Decision | `GO FOR SPRINT 3` or `NO-GO FOR SPRINT 3` |

Helper targets:

```bash
make smoke-api-runtime
make validate-api-openapi
make build-sprint2-release
make test-sprint2-gate
```

Sprint 3 is authorized only when the gate prints **GO FOR SPRINT 3**.

Known limitations remain: no production OIDC, optional live Kafka often unverified, no persistent DLQ/retry topics, no application PostgreSQL/Redis clients, registry loader is local-file/read-only.

Typed local YAML/JSON registry loading. **Not** a plugin system, remote config service, or business validator.

| Item | Behavior |
|------|----------|
| Formats | `.yaml` / `.yml` / `.json` via `yaml.safe_load` path + stdlib JSON |
| Default | `BERGAMA_REGISTRY__ENABLED=false` |
| Paths | Explicit `BERGAMA_REGISTRY__PATHS` only (no repo-wide scan) |
| Schema | Major version `1` only; minor/patch accepted when document validates |
| Fingerprint | SHA-256 over deterministic canonical JSON (not trusted from file) |
| Dependencies | Shallow presence/constraint + cycle/self checks |
| Startup | Loads when enabled + `load_on_startup`; required IDs fail-fast |
| Health | Check name `registry` — skipped when disabled; pass/fail when enabled |
| Out of scope | Remote fetch, hot reload, writes, dynamic imports, type-specific business rules |

Example document shape:

```yaml
registry:
  id: market-data-topics
  type: topic
  version: 1.0.0
  schema_version: 1.0.0
  owner: platform
  created_at: 2026-01-01T00:00:00Z
  dependencies: []
  metadata: {}
payload:
  topics: [events, market-data]
```

Fixtures: `tests/fixtures/registries/`.

## Kafka test runtime (#208B)

Broker-free deterministic harness under `tests/support/kafka/` for validating #208A semantics.

| Item | Behavior |
|------|----------|
| Placement | **Tests only** — never selected by `build_container()` |
| Components | `InMemoryEventBroker`, `FakeEventProducer`, `FakeEventConsumer`, `FakeDlqPublisher` |
| Offsets | Monotonic per topic-partition |
| Partitions | SHA-256(key) mod N; no-key round-robin |
| Commit | Manual; same fail-closed rules as #208A (incl. no commit after DLQ) |
| Live smoke | `make smoke-api-kafka` with `BERGAMA_KAFKA_SMOKE=1` + real bootstrap; topic must exist |

This harness is **not** Kafka and must not be reported as `kafka` health.

## Kafka core runtime (#208A)

| Concern | Behavior |
|---------|----------|
| Client | `aiokafka` only |
| Default | `BERGAMA_KAFKA__ENABLED=false` (local/test stay broker-free) |
| Envelope | Canonical `EventEnvelope` + deterministic JSON + content hash |
| Topics | `TopicRegistry` — `market-data`, `events`, `audit`, `execution`, `risk` |
| Commit | Manual only (`enable_auto_commit` must be false) |
| Retry | In-memory bounded backoff; exhausted + no DLQ → fail-closed (no commit) |
| DLQ | Protocol only — no concrete publisher in #208A |
| Health | Check name `kafka` via cluster metadata (not TCP-only) |
| Lifecycle | Start producer → consumers → workers; stop workers → consumers → producer |

**Limitations**

- Topics are **not** auto-created. Provision them before producing.
- Sprint 1 Kind Kafka advertises `127.0.0.1:9092` (in-pod / port-forward oriented). Cluster-internal clients may need a later infra listener fix; do not treat TCP open as full protocol health.
- Market-data Kafka publish, Iceberg, Schema Registry, retry topics and real DLQ remain Sprint 3+ beyond #302.

## Health runtime (#207)

| Probe | Path | Meaning | HTTP |
|-------|------|---------|------|
| Liveness | `GET /health/live` | Process alive (no deps) | 200 |
| Readiness | `GET /health/ready` | Required deps pass | 200 ready/degraded, 503 not_ready |
| Startup | `GET /health/startup` | Lifespan init complete | 200 started, 503 starting/failed |
| Legacy | `GET /health` | Alias → live | same as live |
| Legacy | `GET /ready` | Alias → ready | same as ready |

Aggregate readiness: all required pass + optional pass → `ready`; required pass + optional fail → `degraded` (200); any required fail/timeout/skipped → `not_ready` (503).

Checks are container-owned (`HealthService`), concurrent, per-check timeout, deterministic order. Responses use `Cache-Control: no-store`.

Default Sprint 2 checks: `postgres_tcp`, `redis_tcp`, and `kafka` (metadata when Kafka enabled; `skipped` when disabled). Postgres/Redis remain connectivity-only until full clients exist.

Policy (defaults): `*_REQUIRED=false` until clients are integrated. Configure via `BERGAMA_POSTGRES_REQUIRED` / `REDIS` / `KAFKA`, hosts, and `BERGAMA_HEALTH_*_TIMEOUT_SECONDS`.

Kubernetes mapping: liveness → `/health/live`, readiness → `/health/ready`, startup → `/health/startup`.

## Dependency container (#206)

Typed application-scoped container. No third-party DI library, no service locator.

| Concern | Behavior |
|---------|----------|
| Type | `AppContainer` (`app/core/container.py`) |
| Builder | `build_container(settings) -> AppContainer` |
| Owns | `settings`, `clock`, `jti_generator`, `token_service` |
| Not owned | request IDs, principals (stay request-scoped / contextvars) |
| App state | `app.state.container` only (canonical) |
| Access | `get_app_container(request)` — typed, fail-fast |
| Factory | `create_app(settings=None, container=None)` |
| Cleanup | `await container.aclose()` (idempotent; for future DB/Redis/Kafka) |
| Tests | Pass an explicit container or build with `FixedClock` / `FixedJtiGenerator` |

```python
from app.core.container import build_container
from app.factory import create_app

container = build_container(settings, clock=FixedClock(...), jti_generator=FixedJtiGenerator("jti"))
app = create_app(container=container)
```

Application-scope deps are created once per app instance. Request-scoped objects must not be stored on the container. There is no global mutable container registry.

Future connection pools (PostgreSQL / Redis / Kafka) will be owned by the same container and released via `aclose()`.

## JWT bootstrap (#205)

Local/test-only HS256 access tokens. **Not** production identity (future OIDC).

| Item | Value |
|------|--------|
| Algorithm | `HS256` (fixed; no alg negotiation) |
| Signing key | `BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY` |
| Enable flag | `BERGAMA_BOOTSTRAP_AUTH_ENABLED` (default: true local/test, false staging/prod) |
| Issuer / audience | `BERGAMA_JWT_ISSUER` / `BERGAMA_JWT_AUDIENCE` (default `bergama-api`) |
| TTL | `BERGAMA_JWT_ACCESS_TOKEN_TTL_SECONDS` (default 900) |
| Mint | `POST /api/v1/auth/token` `{"grant_type":"bootstrap"}` |
| Smoke | `GET /api/v1/auth/me` (Bearer) |
| Staging/prod mint | **404** (`auth.bootstrap_disabled`) |

Fixed bootstrap identity (server-side only): `local-bootstrap-user` / roles `developer` / scopes `api:read`.

No refresh tokens, user DB, passwords, or RBAC.

### Example local flow

```bash
# ensure .secrets.env has BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY (>=32 chars)
curl -sS -X POST http://localhost:8000/api/v1/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"grant_type":"bootstrap"}'

curl -sS http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

Rate limiting is deferred (no Redis). Token responses use `Cache-Control: no-store`.

## Secrets (#204)

| Concern | Behavior |
|---------|----------|
| Model | Nested `AppSettings.secrets` (`SecretSettings`) |
| Types | `pydantic.SecretStr` only |
| Env names | `BERGAMA_SECRETS__APP_SECRET_KEY` (optional), `BERGAMA_SECRETS__BOOTSTRAP_JWT_SIGNING_KEY` |
| Local file | `.secrets.env` (gitignored); template `.secrets.example` |
| Non-secret local | `.env` (gitignored); template `.env.example` |
| Test / staging / production | No `.secrets.env` fallback — inject env only |
| Bootstrap signing key | Required only when `bootstrap_auth_enabled=true` |
| `APP_SECRET_KEY` | Optional — unused by current runtime |
| Access | `settings.secrets.bootstrap_jwt_signing_key.get_secret_value()` |
| Summaries / logs | Configured flags only — never raw values |

### Local setup

```bash
cd apps/api
cp .env.example .env
cp .secrets.example .secrets.env
# edit local-only values; never commit .secrets.env
uv run app
```

### Fail-fast

- Staging/production cannot enable bootstrap auth
- When bootstrap auth is enabled: signing key required, no placeholders, min length 32
- Leading/trailing whitespace on secret values rejected

## Structured logging (#203)

| Concern | Behavior |
|---------|----------|
| Library | Standard library `logging` only (no structlog) |
| Local / test | Human-readable console (no color in test; color only on local TTY) |
| Staging / production | One JSON object per line (`sort_keys=True`) |
| Level | `BERGAMA_LOG_LEVEL` via `AppSettings` |
| Context | `request_id`, `correlation_id`, `causation_id` via `contextvars` |
| Request headers | `X-Request-ID`, `X-Correlation-ID`, `X-Causation-ID` |
| Response headers | Echo / generate the same request + correlation IDs |
| Redaction | Sensitive key names → `[REDACTED]` (nested dicts/lists) |
| Bodies / auth | Never logged |

Bootstrap owner: `create_app()` → `configure_logging(container.settings)` (not import-time, not `main.py`).

### Request ID policy

- Accept inbound IDs only when safe (length ≤ 128, no control chars, `[A-Za-z0-9_-]`).
- Invalid / missing `X-Request-ID` → generate UUID.
- Invalid / missing `X-Correlation-ID` → default to `request_id`.
- Invalid / missing `X-Causation-ID` → omit (never invented).
- Context cleared after every request (no leakage).

### Lifecycle events

| Event | When |
|-------|------|
| `application.starting` / `application.started` | Lifespan startup |
| `application.stopping` / `application.stopped` | Lifespan shutdown |
| `http.request.started` | Middleware (DEBUG for `/health` `/ready`) |
| `http.request.completed` | Middleware (status + `duration_ms`) |
| `http.request.failed` | Uncaught failure / cancellation at middleware |
| `http.exception.unhandled` | Global Exception handler (safe 500 body) |

### Redaction policy

Keys matching (case-insensitive): `password`, `passwd`, `secret`, `token`, `api_key`,
`api-key`, `authorization`, `cookie`, `session`, `credential` (and common variants).
Recursive for nested dicts/lists. Shape preserved. Original mapping not mutated.
Never log raw `AppSettings` dumps.

### Example local log

```text
2026-07-13T00:55:30.522055Z INFO app.lifespan application starting event=application.starting
2026-07-13T00:55:30.927000Z INFO app.middleware.request_context http request completed request_id=… event=http.request.completed status=200 duration_ms=1.2
```

### Example JSON log

```json
{"app_version":"0.2.0","correlation_id":"…","duration_ms":1.2,"environment":"staging","event":"http.request.completed","level":"INFO","logger":"app.middleware.request_context","message":"http request completed","method":"GET","path":"/openapi.json","request_id":"…","service":"bergama-api","source":"middleware","status_code":200,"timestamp":"2026-07-13T00:55:30.927000Z"}
```

## Configuration (#202)

| Item | Value |
|------|--------|
| Prefix | `BERGAMA_` |
| Profiles | `local` \| `test` \| `staging` \| `production` |
| Nested delimiter | `__` |
| Extra env vars | forbidden (`extra=forbid`) |
| Encoding | UTF-8 |

### `.env` policy

- **local** (or unset profile): may load `apps/api/.env` (gitignored)
- **test / staging / production**: process env / injected config only — no `.env` fallback
- Copy `.env.example` → `.env` for local work; never commit secrets

## Setup

```bash
cd apps/api
uv sync --group dev
```

## Run

```bash
uv run app
# or from repo root: make run-api
```

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness (unprefixed) |
| `GET /ready` | Readiness (unprefixed) |
| `GET /docs` | Swagger (if `BERGAMA_DOCS_ENABLED=true`) |
| `GET /openapi.json` | OpenAPI (if `BERGAMA_OPENAPI_ENABLED=true`) |

## Quality gates

```bash
make lint
make typecheck
make test-api
make test-api-container
make test-api-health
make test-api-kafka-core
make test-api-kafka-test-runtime
make test-api-registry
make validate-api-openapi
make smoke-api-runtime
# optional live broker (skipped unless BERGAMA_KAFKA_SMOKE=1):
# make smoke-api-kafka
make build-sprint2-release
make gate-sprint2
```

## Out of scope (#209)

Remote registries, dynamic plugins, hot reload, registry writes, business registry
semantics, UI management, `apps/platform-console` changes.

## Out of scope (#208B)

Production fake fallback, market-data logic, real DLQ, retry topics, Iceberg,
`apps/platform-console` changes.

## Out of scope (#208A)

Market-data connectors, normalization, Iceberg, concrete DLQ, retry topics,
Schema Registry (beyond TopicRegistry), `apps/platform-console` changes.
