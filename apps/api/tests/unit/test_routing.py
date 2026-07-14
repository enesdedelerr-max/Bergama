"""Unit tests for routing keys (#305)."""

from __future__ import annotations

from app.market_data.orchestrator.routing import routing_key_for
from tests.support.orchestrator_events import bar_event, quote_event, trade_event


def test_routing_key_from_canonical_event_type_only() -> None:
    assert routing_key_for(trade_event()) == "market.trade"
    assert routing_key_for(quote_event()) == "market.quote"
    assert routing_key_for(bar_event()) == "market.bar"
