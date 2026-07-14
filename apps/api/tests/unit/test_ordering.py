"""Unit tests for ordering tracker (#305)."""

from __future__ import annotations

from datetime import timedelta

from app.market_data.orchestrator.ordering import OrderingTracker
from tests.support.orchestrator_events import EVENT_TIME, equity, quote_event, trade_event


def test_ordering_is_per_instrument_and_event_type() -> None:
    tracker = OrderingTracker()
    aapl_trade = trade_event(source_event_id="t1")
    aapl_quote = quote_event(source_event_id="q1")
    msft_trade = trade_event(
        source_event_id="t2",
        instrument=equity(key="bergama:equity:us:msft", symbol="MSFT"),
    )
    d1 = tracker.observe(aapl_trade)
    d2 = tracker.observe(aapl_quote)
    d3 = tracker.observe(msft_trade)
    d4 = tracker.observe(trade_event(source_event_id="t3"))
    assert d1.scope != d2.scope
    assert d1.scope != d3.scope
    assert d1.sequence == 1
    assert d4.sequence == 2
    assert d4.scope == d1.scope


def test_ordering_detects_out_of_order_without_reordering() -> None:
    tracker = OrderingTracker()
    first = tracker.observe(trade_event(source_event_id="a", occurred_at=EVENT_TIME))
    second = tracker.observe(
        trade_event(source_event_id="b", occurred_at=EVENT_TIME - timedelta(minutes=1))
    )
    third = tracker.observe(
        trade_event(source_event_id="c", occurred_at=EVENT_TIME + timedelta(minutes=1))
    )
    assert first.out_of_order is False
    assert second.out_of_order is True
    assert third.out_of_order is False
    assert [first.sequence, second.sequence, third.sequence] == [1, 2, 3]
