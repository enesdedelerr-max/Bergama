# Bergama API — Sprint 2 Runtime Foundation

FastAPI runtime for the AI Hedge Fund Operating System.

## Issue status

- ✅ **#201** Runtime Bootstrap
- 🟡 **#202** Configuration Layer (current)
- Later: logging, auth, DI, DB, Kafka

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

### Fail-fast examples

- `production` or `staging` with `BERGAMA_DEBUG=true`
- `production` with `BERGAMA_LOG_LEVEL=DEBUG`
- invalid `BERGAMA_API_PREFIX` (must start with `/`, no trailing `/` unless `/`)
- unknown environment string
- non-positive timeouts

### Tests

`clear_settings_cache()` runs automatically via an autouse fixture. Override with explicit `AppSettings(...)` or `monkeypatch.setenv`.

### Local override

```bash
cd apps/api
cp .env.example .env
# edit BERGAMA_* values
uv run app
```

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
```

## Out of scope (#202)

JWT, PostgreSQL, Redis, Kafka, Vault, DI container, trading logic.
