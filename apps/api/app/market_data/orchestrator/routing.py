"""Canonical event-type routing keys (#305).

No Kafka topic names and no provider branching.
"""

from __future__ import annotations

from app.market_data.enums import MarketEventType
from app.market_data.envelope import CanonicalMarketEvent

_ROUTING_PREFIX = "market"


def routing_key_for(event: CanonicalMarketEvent) -> str:
    """Return a stable routing key derived only from canonical event type."""
    event_type = event.event_type
    if not isinstance(event_type, MarketEventType):
        msg = "event_type must be a MarketEventType"
        raise TypeError(msg)
    return f"{_ROUTING_PREFIX}.{event_type.value}"
