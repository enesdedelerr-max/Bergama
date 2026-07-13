# Sprint 2 — FastAPI Runtime Foundation

## Status

In progress. Issue **#201 FastAPI Runtime Bootstrap** is the entry point.

## Goal

Establish the production FastAPI runtime that every later sprint builds on.

## Issue chain

1. **#201** FastAPI Project Bootstrap
2. **#202** Configuration Layer
3. **#203** Logging
4. **#204** Health API
5. **#205** Auth Bootstrap
6. **#206** Dependency Injection
7. **#207** Database Layer
8. **#208** Kafka Layer
9. **#209** OpenAPI
10. **#210** Runtime Smoke Tests
11. **Sprint 2 Gate**

## Package

[`apps/api`](../../apps/api) — Python 3.13, FastAPI, Pydantic v2, uv.

## Commands

```bash
cd apps/api && uv sync --group dev
make lint
make typecheck
make test-api
make run-api
```

## Constraints

- Do not modify Sprint 1 infrastructure except for defects.
- No market data, broker, or trading logic until later sprints.
