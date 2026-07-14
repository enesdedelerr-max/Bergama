"""JSON-safe payload conversion for EventEnvelope compatibility.

Domain models remain Decimal-native. Transport payloads use canonical
Decimal strings and sorted keys — Sprint 2 ``serialize_event`` is unchanged.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from app.events.envelope import EventEnvelope
from app.market_data.envelope import CanonicalMarketEvent, parse_canonical_market_event
from app.market_data.keys import build_idempotency_key
from app.market_data.money import canonical_decimal_str

CANONICAL_MARKET_SCHEMA_VERSION = "1.0.0"
_SOURCE_SYSTEM = "bergama-market-data"


def market_event_to_payload(event: CanonicalMarketEvent) -> dict[str, Any]:
    """Convert a canonical event to a JSON-safe mapping for EventEnvelope.payload."""
    raw = event.model_dump(mode="python")
    converted = _to_json_safe(raw)
    if not isinstance(converted, dict):
        msg = "market event payload must be an object"
        raise TypeError(msg)
    return {str(key): value for key, value in converted.items()}


def market_event_from_payload(payload: dict[str, Any]) -> CanonicalMarketEvent:
    """Parse payload produced by ``market_event_to_payload``."""
    return parse_canonical_market_event(payload)


def market_event_to_envelope(
    event: CanonicalMarketEvent,
    *,
    event_id: UUID | None = None,
    correlation_id: str | None = None,
    causation_id: str | None = None,
    metadata: dict[str, str] | None = None,
) -> EventEnvelope:
    """Wrap a canonical market event in a Sprint 2 EventEnvelope.

    Mapping:
    - ``EventEnvelope.occurred_at`` ← ``event.occurred_at``
    - ``EventEnvelope.ingested_at`` ← ``event.ingested_at``
    - PIT quartet remains inside payload
    """
    payload = market_event_to_payload(event)
    return EventEnvelope(
        event_id=event_id or uuid4(),
        event_type=f"market.{event.event_type.value}",
        schema_version=event.schema_version,
        source_system=_SOURCE_SYSTEM,
        occurred_at=event.occurred_at,
        ingested_at=event.ingested_at,
        correlation_id=correlation_id,
        causation_id=causation_id,
        idempotency_key=build_idempotency_key(event),
        payload=payload,
        metadata=metadata,
    )


def _to_json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _to_json_safe(v) for k, v in sorted(value.items(), key=lambda i: str(i[0]))}
    if isinstance(value, (list, tuple)):
        return [_to_json_safe(item) for item in value]
    if isinstance(value, Decimal):
        return canonical_decimal_str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, float):
        msg = "binary float values are not allowed in market payloads"
        raise TypeError(msg)
    return value
