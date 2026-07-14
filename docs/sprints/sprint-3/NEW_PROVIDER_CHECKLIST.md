# Provider Onboarding Guide

Every new market-data provider must include:

1. **Typed provider settings** — `apps/api/app/core/<provider>_settings.py`; disabled by default; validated bounds; `safe_summary()`.
2. **Explicit authentication boundary** — credentials never appear in query strings, logs, errors, sanitized URLs, or event provenance.
3. **SecretStr for credentials** — use Pydantic `SecretStr` (or documented non-secret auth such as SEC User-Agent/contact).
4. **Async HTTP or WebSocket transport** — dedicated client/session modules; no sync I/O on the event loop.
5. **Bounded retry policy** — connection/timeout/429/5xx only; honor capped `Retry-After`; no retry on 400/401/403/404/schema/mapping failures.
6. **Explicit pagination or streaming policy** — official provider model; max pages/cursors; loop/regression detection; no silent truncation or silent dedupe. Document single-response APIs when pagination does not apply.
7. **Provider-specific response schemas** — typed parse models for API/WS payloads; reject unexpected shapes fail-closed.
8. **Canonical event mapper** — map to `#301` `CanonicalMarketEvent` types; caller-owned `InstrumentId`; no inferred canonical identity; UTC PIT timestamps.
9. **SourceReference provenance** — correct `provider` literal; stable `source_event_id`; provider IDs in source/extras only; no credentials; no raw body dumps.
10. **Deterministic idempotency and deduplication keys** — via `build_idempotency_key` / `build_deduplication_key` after mapping; keys stable across runs for the same event.
11. **Container-owned lifecycle** — construct when enabled in `AppContainer`; close HTTP/WS resources in `aclose`; no leaked sessions.
12. **Offline synthetic fixtures** — `tests/support/provider_contracts/<provider>.py`; deterministic; no real keys; no copyrighted bodies.
13. **Cross-provider contract matrix entry** — one row (or fixture set) in each `tests/contract/test_provider_*_contracts.py` dimension.
14. **Provider-focused tests** — unit/contract coverage for schemas, mapper, retry, pagination, and connector facade.
15. **Optional live smoke test** — env-gated (`BERGAMA_<PROVIDER>_SMOKE=1` pattern); default SKIPPED.

---

## Certification rule

A provider is **not production-ready** until **all** of the following pass:

```bash
make lint
make typecheck
make validate-secrets
make test-api-<provider-focused-target>   # e.g. test-api-benzinga-news
make test-api-provider-contracts
make test-api
```

Live smoke may be **SKIPPED** when credentials or entitlement are unavailable.
**Offline contract validation is mandatory** — live smoke never substitutes for
`make test-api-provider-contracts`.

Rules:

- Focused unit tests alone are insufficient.
- Live smoke alone is insufficient.
- Passing `make test-api-provider-contracts` is required for Sprint 3 connector certification.

---

## Expected extension process

1. Add settings (`<provider>_settings.py` + wire into `AppSettings`).
2. Add transport/client (HTTP and/or WebSocket + auth/redaction).
3. Add provider schemas.
4. Add mapper to canonical events + SourceReference.
5. Add synthetic fixtures under `tests/support/provider_contracts/`.
6. Add contract matrix rows in `tests/contract/test_provider_*_contracts.py`.
7. Add provider-focused tests (+ optional env-gated live smoke).
8. Run the full provider gate (certification commands above).

Wire DI into `AppContainer` when the provider is enabled (construct + `aclose`).
That registration is explicit today until a later plugin/orchestrator layer.

---

## Architectural rule

Adding a new provider should **normally** require only:

- provider-specific settings,
- client/transport,
- schemas,
- mapper,
- fixtures,
- contract matrix rows,
- focused tests,
- optional live smoke.

If production **shared** runtime changes are required, the PR must explain why the
existing provider boundary is insufficient.

---

## Explicit non-goals (provider PRs)

Do **not** include in a provider onboarding PR:

- a new provider SDK framework or registry runtime,
- orchestration / scheduling / polling loops,
- Kafka publish,
- Iceberg writes,
- provider fallback or arbitration,
- symbol master resolution inside the connector,
- `#305` Market Data Orchestrator code,
- strategy, execution, or UI work.

---

## Definition of done

- [ ] All 15 checklist items implemented
- [ ] Certification commands PASS (live smoke may SKIP)
- [ ] No secrets in provenance, logs, errors, or sanitized URLs
- [ ] Diff limited to provider-local + fixtures/tests/docs (or justified shared-runtime change)
