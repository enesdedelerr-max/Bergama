# Bergama API (Sprint 2)

FastAPI runtime foundation for the AI Hedge Fund Operating System.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
cd apps/api
uv sync --group dev
```

## Run

```bash
uv run app
# or from repo root:
make run-api
```

Default listen address: `http://0.0.0.0:8000`

- `GET /health` — liveness
- `GET /ready` — readiness (config loaded; no external deps in #201)
- `GET /docs` — Swagger UI
- `GET /openapi.json` — OpenAPI document

## Quality gates

From repo root:

```bash
make lint
make typecheck
make test-api
```

From `apps/api`:

```bash
uv run ruff check app tests
uv run mypy
uv run pytest
```

## Configuration

Environment variables use the `BERGAMA_` prefix (see `.env.example`).

## Layout

```text
app/
  api/              HTTP routers
  config/           Settings
  core/             Logging, lifespan, DI
  domain/           Domain (empty in #201)
  application/      Use cases (empty in #201)
  infrastructure/   Adapters (empty in #201)
tests/
```

No market data, broker, or trading logic in this package for Issue #201.
