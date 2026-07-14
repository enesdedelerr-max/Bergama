# Sprint 2 — FastAPI Runtime Foundation

## Status

✅ Issues **#201–#209** delivered on the Sprint 2 stack  
✅ Issue **#210** Runtime Smoke Tests and Sprint 2 Gate — `make gate-sprint2`

Do **not** start Sprint 3 until `make gate-sprint2` reports **GO FOR SPRINT 3**.

## Goal

Establish the production FastAPI runtime that every later sprint builds on.

## Issue chain

1. ✅ **#201** FastAPI Runtime Bootstrap
2. ✅ **#202** Configuration Layer
3. ✅ **#203** Structured Logging
4. ✅ **#204** Settings & Secrets
5. ✅ **#205** JWT Bootstrap
6. ✅ **#206** Dependency Injection
7. ✅ **#207** Health Runtime
8. ✅ **#208A** Kafka Core Runtime
9. ✅ **#208B** Kafka Test Runtime
10. ✅ **#209** Registry Loader
11. ✅ **#210** Runtime Smoke Tests and Sprint 2 Gate

Trading Engine Foundation (#211) is **out of scope** for this gate.

## Package

[`apps/api`](../../apps/api) — Python 3.13, FastAPI, Pydantic v2, uv, PyJWT.

## Commands

```bash
cd apps/api && uv sync --group dev
make lint
make typecheck
make validate-secrets
make test-api
make test-api-auth
make test-api-container
make test-api-health
make test-api-kafka-core
make test-api-kafka-test-runtime
make test-api-registry
make validate-api-openapi
make smoke-api-runtime
make smoke-api-kafka          # optional live broker; SKIPPED unless BERGAMA_KAFKA_SMOKE=1
make build-sprint2-release
make gate-sprint2             # fail-closed Sprint 2 gate
make test-sprint2-gate        # unit tests for the gate orchestrator
```

## Gate (#210)

`make gate-sprint2` is fail-closed. Required checks must PASS. Optional live Kafka may be **SKIPPED**.

| Class | Checks |
|-------|--------|
| Required | lint, typecheck, validate-secrets, all Sprint 2 API test targets, OpenAPI validation, runtime smoke, release package + checksums |
| Optional | `smoke-api-kafka` — PASS if enabled and green; SKIPPED if not enabled; FAIL only when enabled and failing |

Live Kafka SKIPPED does **not** fail Sprint 2; broker-free #208A/#208B remains the certified baseline.

Artifacts:

- `artifacts/sprint2/gate-summary.json` / `.txt`
- `artifacts/sprint2/evidence/`
- `reports/sprint2-runtime-validation.json`
- `releases/sprint-2/`

Final decision is exactly `GO FOR SPRINT 3` or `NO-GO FOR SPRINT 3`.

## Constraints

- Do not modify Sprint 1 infrastructure except for defects.
- Do not start Sprint 3 market-data work until the gate is GO.
- No production OIDC in Sprint 2.
