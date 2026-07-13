# Sprint 2 — FastAPI Runtime Foundation

## Status

🟡 Issue **#205 JWT Bootstrap** — in progress on `feature/sprint2-issue205-jwt-bootstrap`

✅ Issue **#204** Settings & Secrets  
✅ Issue **#203** Structured Logging  
✅ Issue **#202** Configuration Layer  
✅ Issue **#201** Runtime Bootstrap

## Goal

Establish the production FastAPI runtime that every later sprint builds on.

## Issue chain

1. ✅ **#201** FastAPI Runtime Bootstrap
2. ✅ **#202** Configuration Layer
3. ✅ **#203** Structured Logging
4. ✅ **#204** Settings & Secrets
5. 🟡 **#205** JWT Bootstrap
6. ⏳ **#206** Dependency Injection
7. ⏳ **#207** Health Runtime
8. ⏳ **#208** Kafka Runtime
9. ⏳ **#210** Runtime Smoke Tests
10. **Sprint 2 Gate**

## Package

[`apps/api`](../../apps/api) — Python 3.13, FastAPI, Pydantic v2, uv, PyJWT.

## Commands

```bash
cd apps/api && uv sync --group dev
make lint
make typecheck
make test-api
make test-api-auth
make validate-secrets
make run-api
```

## Constraints

- Do not modify Sprint 1 infrastructure except for defects.
- No OIDC, refresh tokens, user DB, Redis, Kafka, or trading logic in #201–#205.
