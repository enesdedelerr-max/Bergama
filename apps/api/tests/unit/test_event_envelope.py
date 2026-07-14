"""Unit tests for EventEnvelope validation."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.events.envelope import EventEnvelope
from pydantic import ValidationError


def _base(**overrides: object) -> EventEnvelope:
    data: dict[str, object] = {
        "event_id": uuid4(),
        "event_type": "market.quote.received",
        "schema_version": "1",
        "source_system": "bergama-api",
        "occurred_at": datetime(2026, 7, 12, 12, 0, 0, tzinfo=UTC),
        "ingested_at": datetime(2026, 7, 12, 12, 0, 1, tzinfo=UTC),
        "idempotency_key": "idem-1",
        "payload": {"symbol": "AAPL"},
    }
    data.update(overrides)
    return EventEnvelope.model_validate(data)


def test_event_envelope_validation() -> None:
    event = _base()
    assert event.event_type == "market.quote.received"
    assert event.payload["symbol"] == "AAPL"


def test_utc_timestamps_required() -> None:
    with pytest.raises(ValidationError):
        _base(occurred_at=datetime(2026, 7, 12, 12, 0, 0))


def test_idempotency_key_required() -> None:
    with pytest.raises(ValidationError):
        _base(idempotency_key="")
