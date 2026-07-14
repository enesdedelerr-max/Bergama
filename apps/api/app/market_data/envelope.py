"""Discriminated CanonicalMarketEvent union."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, TypeAdapter, ValidationError

from app.market_data.events.bar import BarEvent
from app.market_data.events.filing import FilingEvent
from app.market_data.events.fundamental import FundamentalEvent
from app.market_data.events.macro import MacroEvent
from app.market_data.events.news import NewsEvent
from app.market_data.events.quote import QuoteEvent
from app.market_data.events.reference import ReferenceDataEvent
from app.market_data.events.trade import TradeEvent

type CanonicalMarketEvent = Annotated[
    QuoteEvent
    | TradeEvent
    | BarEvent
    | ReferenceDataEvent
    | FundamentalEvent
    | MacroEvent
    | FilingEvent
    | NewsEvent,
    Field(discriminator="event_type"),
]

_ADAPTER: TypeAdapter[CanonicalMarketEvent] = TypeAdapter(CanonicalMarketEvent)


def parse_canonical_market_event(data: object) -> CanonicalMarketEvent:
    """Validate a mapping into a discriminated canonical market event."""
    try:
        return _ADAPTER.validate_python(data)
    except ValidationError as exc:
        msg = "malformed canonical market event payload"
        raise ValueError(msg) from exc
