# Bergama API — Sprint 2 Issue #201 Runtime Bootstrap

Production-grade FastAPI runtime foundation. This package is bootstrap only:
no JWT, database, Redis, Kafka, market data, broker, or trading logic.

## Layout

```text
apps/api/
├── app/
│   ├── main.py           # process entry (`uv run app`)
│   ├── factory.py        # FastAPI app factory
│   ├── lifespan.py       # startup / shutdown
│   ├── routers/
│   │   └── health.py     # GET /health, GET /ready
│   ├── middleware/       # reserved (empty in #201)
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   └── __init__.py
├── tests/
│   ├── smoke/
│   └── unit/
└── README.md
```

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

Default: `http://0.0.0.0:8000`

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness |
| `GET /ready` | Readiness (runtime ready; no external deps yet) |
| `GET /docs` | Swagger UI |
| `GET /openapi.json` | OpenAPI document |

## Quality gates

```bash
make lint
make typecheck
make test-api
# or: cd apps/api && uv run pytest
```

## Configuration

Environment variables use the `BERGAMA_` prefix. See `.env.example`.

## Next

Issue **#202 — Configuration Layer**
