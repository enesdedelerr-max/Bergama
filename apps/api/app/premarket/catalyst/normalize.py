"""Adapters that accept approved NewsEvent inputs without mutating Market Data."""

from __future__ import annotations

from collections.abc import Sequence

from app.market_data.events.news import NewsEvent
from app.premarket.errors import CatalystUnsupportedEventError, CatalystValidationError


def coerce_news_events(events: Sequence[object] | object) -> tuple[NewsEvent, ...]:
    """Coerce an ordered sequence into frozen ``NewsEvent`` instances."""
    if isinstance(events, NewsEvent):
        return (events,)
    if not isinstance(events, (list, tuple)):
        raise CatalystValidationError(detail="events_must_be_sequence")
    coerced: list[NewsEvent] = []
    for index, item in enumerate(events):
        coerced.append(_coerce_one(item, index=index))
    return tuple(coerced)


def _coerce_one(item: object, *, index: int) -> NewsEvent:
    if isinstance(item, NewsEvent):
        return item
    if isinstance(item, dict):
        try:
            return NewsEvent.model_validate(item)
        except Exception as exc:
            raise CatalystUnsupportedEventError(
                detail=f"invalid_news_event_at_{index}:{exc}"
            ) from exc
    raise CatalystUnsupportedEventError(
        detail=f"unsupported_event_type:{type(item).__name__}:index={index}"
    )
