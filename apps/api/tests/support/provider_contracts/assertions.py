"""Provider-agnostic assertions for market-data connector contracts (#304E)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.events.serialization import deserialize_event, serialize_event
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.events.base import MarketEventBase
from app.market_data.identity import InstrumentId
from app.market_data.keys import build_deduplication_key, build_idempotency_key
from app.market_data.money import canonical_decimal_str
from app.market_data.serialization import (
    market_event_from_payload,
    market_event_to_envelope,
    market_event_to_payload,
)
from app.market_data.source import SourceReference

_CREDENTIAL_FRAGMENTS = (
    "password",
    "secret",
    "api_key",
    "apikey",
    "authorization",
    "bearer ",
    "token=",
)


def assert_identity_contract(
    event: MarketEventBase,
    *,
    caller_instrument: InstrumentId,
    provider_identifier: str | None = None,
) -> None:
    """Caller InstrumentId survives; provider id is never canonical identity."""
    assert event.instrument.instrument_key == caller_instrument.instrument_key
    assert event.instrument == caller_instrument
    if provider_identifier:
        assert event.instrument.instrument_key != provider_identifier
        assert event.instrument.instrument_key != provider_identifier.strip().upper()
        assert event.instrument.instrument_key != provider_identifier.strip().lower()


def assert_pit_contract(event: MarketEventBase) -> None:
    """All PIT timestamps are UTC-aware and ordered."""
    for name in ("occurred_at", "effective_at", "known_at", "ingested_at"):
        value = getattr(event, name)
        assert isinstance(value, datetime)
        assert value.tzinfo is not None
        assert value.utcoffset() is not None
    assert event.occurred_at <= event.known_at
    if not event.quality.is_late:
        assert event.known_at <= event.ingested_at


def assert_key_contract(event: MarketEventBase) -> None:
    """Deterministic key builders are stable for the same event."""
    first_idem = build_idempotency_key(event)  # type: ignore[arg-type]
    second_idem = build_idempotency_key(event)  # type: ignore[arg-type]
    first_dedup = build_deduplication_key(event)  # type: ignore[arg-type]
    second_dedup = build_deduplication_key(event)  # type: ignore[arg-type]
    assert first_idem == second_idem
    assert first_dedup == second_dedup
    assert first_idem
    assert first_dedup


def assert_keys_distinct(left: MarketEventBase, right: MarketEventBase) -> None:
    assert build_idempotency_key(left) != build_idempotency_key(right)  # type: ignore[arg-type]
    assert build_deduplication_key(left) != build_deduplication_key(right)  # type: ignore[arg-type]


def assert_decimal_fields_finite(event: MarketEventBase, fields: tuple[str, ...]) -> None:
    payload = market_event_to_payload(event)  # type: ignore[arg-type]
    for field in fields:
        value = getattr(event, field)
        if value is None:
            continue
        assert isinstance(value, Decimal)
        assert value.is_finite()
        assert payload[field] == canonical_decimal_str(value)
        assert "nan" not in str(payload[field]).lower()
        assert "inf" not in str(payload[field]).lower()


def assert_provenance_contract(
    event: MarketEventBase,
    *,
    provider: str,
    source_event_id: str | None = None,
) -> None:
    source = event.source
    assert isinstance(source, SourceReference)
    assert source.provider == provider
    if source_event_id is not None:
        assert source.source_event_id == source_event_id
    assert source.source_event_id
    blob = str(source.model_dump(mode="python")).lower()
    for fragment in _CREDENTIAL_FRAGMENTS:
        assert fragment not in blob
    assert "raw_body" not in source.extras
    assert "response_body" not in source.extras


def assert_redaction_contract(*texts: str | None) -> None:
    """Secret/material fragments must not appear in diagnostic strings."""
    for text in texts:
        if text is None:
            continue
        lowered = text.lower()
        for fragment in (
            "authorization: bearer",
            "authorization: token",
            "x-finnhub-token",
            "api_key=",
            "apikey=",
            "token=",
        ):
            assert fragment not in lowered, f"credential fragment {fragment!r} leaked"


def assert_event_envelope_contract(event: CanonicalMarketEvent) -> None:
    envelope = market_event_to_envelope(
        event,
        event_id=UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
    )
    assert envelope.occurred_at == event.occurred_at
    assert envelope.ingested_at == event.ingested_at
    assert envelope.idempotency_key == build_idempotency_key(event)
    assert envelope.event_type == f"market.{event.event_type.value}"
    raw = serialize_event(envelope)
    restored = deserialize_event(raw)
    parsed = market_event_from_payload(restored.payload)
    assert parsed.event_type == event.event_type
    assert parsed.instrument.instrument_key == event.instrument.instrument_key
    assert parsed.source.provider == event.source.provider
    assert parsed.source.source_event_id == event.source.source_event_id
    assert build_idempotency_key(parsed) == build_idempotency_key(event)
    assert market_event_to_payload(parsed) == restored.payload


def secret_absent_in_mapping(data: dict[str, Any], secrets: tuple[str, ...]) -> None:
    blob = str(data).lower()
    for secret in secrets:
        assert secret.lower() not in blob
