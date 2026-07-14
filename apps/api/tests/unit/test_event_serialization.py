"""Unit tests for deterministic event serialization."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from app.events.envelope import EventEnvelope
from app.events.errors import EventHashMismatchError, EventSerializationError
from app.events.serialization import compute_content_hash, deserialize_event, serialize_event

_FIXED_ID = UUID("11111111-1111-1111-1111-111111111111")


def _event(**overrides: object) -> EventEnvelope:
    data: dict[str, object] = {
        "event_id": _FIXED_ID,
        "event_type": "market.quote.received",
        "schema_version": "1",
        "source_system": "bergama-api",
        "occurred_at": datetime(2026, 7, 12, 12, 0, 0, tzinfo=UTC),
        "ingested_at": datetime(2026, 7, 12, 12, 0, 1, tzinfo=UTC),
        "idempotency_key": "idem-1",
        "payload": {"b": 2, "a": 1},
        "metadata": {"z": "9", "m": "1"},
    }
    data.update(overrides)
    return EventEnvelope.model_validate(data)


def test_deterministic_serialization() -> None:
    first = serialize_event(_event())
    second = serialize_event(_event())
    assert first == second


def test_content_hash_stable_across_key_order() -> None:
    left = _event(payload={"a": 1, "b": 2})
    right = _event(payload={"b": 2, "a": 1})
    assert compute_content_hash(left) == compute_content_hash(right)


def test_hash_mismatch_rejected() -> None:
    import json

    raw = serialize_event(_event())
    payload = json.loads(raw.decode("utf-8"))
    payload["content_hash"] = "0" * 64
    with pytest.raises(EventHashMismatchError):
        deserialize_event(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())


def test_unsupported_payload_value_rejected() -> None:
    event = _event(payload={"x": float("nan")})
    with pytest.raises(EventSerializationError):
        serialize_event(event)


def test_roundtrip_preserves_schema_version() -> None:
    original = _event()
    restored = deserialize_event(serialize_event(original))
    assert restored.schema_version == "1"
    assert restored.event_id == original.event_id
    assert restored.content_hash == compute_content_hash(original)
