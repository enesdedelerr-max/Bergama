# Bergama API — Sprint 2 Runtime Foundation

FastAPI runtime for the AI Hedge Fund Operating System.

## Issue status

- ✅ **#201** Runtime Bootstrap
- ✅ **#202** Configuration Layer
- 🟡 **#203** Structured Logging (current)
- Later: auth, DI, DB, Kafka

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

Bootstrap owner: `create_app()` → `configure_logging(settings)` (not import-time, not `main.py`).

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
# or focused:
cd apps/api && uv run pytest tests/unit/test_logging.py tests/unit/test_log_context.py tests/integration/test_request_logging.py
```

## Out of scope (#203)

JWT/OIDC, user identity logging, PostgreSQL/Redis/Kafka logging, OpenTelemetry exporters,
Prometheus, DI container, audit/business-event logging, Loki/Helm/log shipping,
`apps/platform-console` changes.
