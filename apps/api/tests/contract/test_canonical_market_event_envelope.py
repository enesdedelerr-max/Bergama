"""Contract tests: canonical market events ↔ Sprint 2 EventEnvelope."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import pytest
from app.events.serialization import deserialize_event, serialize_event
from app.market_data.envelope import parse_canonical_market_event
from app.market_data.keys import build_idempotency_key
from app.market_data.serialization import (
    market_event_from_payload,
    market_event_to_envelope,
    market_event_to_payload,
)
from tests.support.market_data_fixtures import (
    make_bar,
    make_filing,
    make_fundamental,
    make_macro,
    make_news,
    make_quote,
    make_reference,
    make_trade,
)

_FIXED_ID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


@pytest.mark.parametrize(
    "factory",
    [
        make_quote,
        make_trade,
        make_bar,
        make_reference,
        make_fundamental,
        make_macro,
        make_filing,
        make_news,
    ],
)
def test_event_envelope_round_trip(factory: object) -> None:
    event = factory()  # type: ignore[operator]
    envelope = market_event_to_envelope(event, event_id=_FIXED_ID)
    assert envelope.occurred_at == event.occurred_at
    assert envelope.ingested_at == event.ingested_at
    assert envelope.idempotency_key == build_idempotency_key(event)
    assert envelope.event_type == f"market.{event.event_type.value}"
    assert isinstance(envelope.payload["schema_version"], str)
    # Decimal values must be strings in transport payload.
    raw = serialize_event(envelope)
    restored = deserialize_event(raw)
    assert restored.event_id == _FIXED_ID
    assert restored.idempotency_key == envelope.idempotency_key
    parsed = market_event_from_payload(restored.payload)
    assert parsed.event_type == event.event_type
    assert parsed.instrument.instrument_key == event.instrument.instrument_key
    assert market_event_to_payload(parsed) == restored.payload


def test_payload_conversion_uses_decimal_strings() -> None:
    payload = market_event_to_payload(make_trade(price=Decimal("10.500")))
    assert payload["price"] == "10.5"
    assert "float" not in str(type(payload["price"]))


def test_malformed_payload_rejection() -> None:
    with pytest.raises(ValueError, match="malformed"):
        parse_canonical_market_event({"event_type": "quote"})
    with pytest.raises(ValueError, match="malformed"):
        parse_canonical_market_event({"event_type": "not-a-type", "schema_version": "1.0.0"})


def test_envelope_payload_preserves_source_without_provider_top_level_leakage() -> None:
    event = make_quote()
    payload = market_event_to_payload(event)
    assert "polygon_ticker" not in payload
    assert payload["source"]["provider"] == "polygon"
    assert payload["source"]["source_symbol"] == "AAPL"
