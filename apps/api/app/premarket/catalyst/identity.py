"""Deterministic catalyst record identity."""

from __future__ import annotations

from app.market_data.events.news import NewsEvent
from app.strategy.keys import strategy_sha256

_IDENTITY_SCHEMA = "premarket.catalyst.record.v1"


def build_catalyst_record_id(event: NewsEvent) -> str:
    """Return a stable sha256 hex identity for a NewsEvent.

    Provider ``source_event_id`` is included when present but is never the sole
    identity root. Identical semantic payloads always hash to the same id.
    """
    return strategy_sha256(
        {
            "schema": _IDENTITY_SCHEMA,
            "event_type": event.event_type.value,
            "schema_version": event.schema_version,
            "instrument_key": event.instrument.instrument_key,
            "occurred_at": event.occurred_at,
            "known_at": event.known_at,
            "provider": event.source.provider,
            "source_event_id": event.source.source_event_id or "",
            "headline": event.headline,
            "summary": event.summary or "",
            "url_ref": event.url_ref or "",
            "topics": list(event.topics),
        }
    )


def declared_source_identity(event: NewsEvent) -> tuple[str, str] | None:
    """Provider-scoped source identity used for conflict detection.

    Returns ``None`` when the provider event id is absent; identity then rests
    solely on the content-derived ``catalyst_record_id``.
    """
    source_event_id = event.source.source_event_id
    if source_event_id is None:
        return None
    return (event.source.provider, source_event_id)
