# TD-KAFKA-TEST-001 — Kafka test runtime hardening

| Field | Value |
|-------|-------|
| ID | TD-KAFKA-TEST-001 |
| Severity | Low |
| Status | Accepted |
| Component | `apps/api` Kafka test harness (`tests/support/kafka/`) |
| Origin | Sprint 2 — Issue #208B (PR #20) |
| Action | Optional hardening in a later non-blocking follow-up |

## Summary

Issue #208B delivered a broker-free Kafka test runtime that is accepted as complete for Sprint 2. A few hardening items remain relative to a later expanded checklist; none block Sprint 2 progress or #209/#210.

## Current accepted behavior

- Production modules do not import test fakes.
- Broker-free producer/consumer round-trips and real `ConsumerWorker` semantics are covered.
- Production `serialize_event` / `deserialize_event` are reused.
- Manual commit and fail-closed (including DLQ) behavior are tested.
- Normal CI remains broker-free (`kafka_integration` deselected).
- Live Kafka smoke is opt-in (`BERGAMA_KAFKA_SMOKE=1`) and reports SKIPPED honestly.

## Non-blocking gaps

1. Support layout could split `handlers.py` / `harness.py` / `models.py` from `fixtures.py`.
2. Dedicated `test_fake_kafka_dlq.py` unit file (DLQ already covered in integration).
3. Duplicate topic create with identical partition count could be idempotent (today always fails).
4. Consumer empty-queue wait uses poll sleep; prefer `asyncio.Event` / `Condition`.
5. Invalid commit order not strictly rejected.
6. Same consumer-group concurrent consumers assumed single-active, not hard-enforced.
7. Smoke env name is `BERGAMA_KAFKA_SMOKE=1` rather than `BERGAMA_KAFKA_SMOKE_ENABLED=true`.

## Decision

Accept #208B / PR #20 as complete for Sprint 2. Do not reopen PR #20 for these items unless a test flake or semantic defect appears.

## Exit criteria

Close this TD when a follow-up PR addresses the items above (or explicitly closes them as wont-fix with rationale) without weakening production Kafka semantics.
