"""Adapters that accept approved BarEvent inputs without mutating Market Data."""

from __future__ import annotations

from collections.abc import Sequence

from app.market_data.events.bar import BarEvent
from app.premarket.errors import GapUnsupportedEventError, GapValidationError


def coerce_bar_events(bars: Sequence[object] | object) -> tuple[BarEvent, ...]:
    """Coerce an ordered sequence into frozen ``BarEvent`` instances."""
    if isinstance(bars, BarEvent):
        return (bars,)
    if not isinstance(bars, (list, tuple)):
        raise GapValidationError(detail="bars_must_be_sequence")
    coerced: list[BarEvent] = []
    for index, item in enumerate(bars):
        coerced.append(_coerce_one(item, index=index))
    return tuple(coerced)


def _coerce_one(item: object, *, index: int) -> BarEvent:
    if isinstance(item, BarEvent):
        return item
    if isinstance(item, dict):
        try:
            return BarEvent.model_validate(item)
        except Exception as exc:
            raise GapUnsupportedEventError(detail=f"invalid_bar_event_at_{index}:{exc}") from exc
    raise GapUnsupportedEventError(
        detail=f"unsupported_event_type:{type(item).__name__}:index={index}"
    )
