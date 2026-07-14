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
