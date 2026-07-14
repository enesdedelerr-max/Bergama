"""Synthetic Polygon fixtures mapped to canonical events."""

from __future__ import annotations

from app.core.clock import Clock
from app.infrastructure.polygon.mapper import map_bar_event
from app.infrastructure.polygon.schemas import PolygonAggBar, PolygonAggsResponse
from app.infrastructure.polygon.ws_mapper import map_ws_minute_bar, map_ws_quote, map_ws_trade
from app.infrastructure.polygon.ws_schemas import (
    PolygonWsMinuteAggregateMessage,
    PolygonWsQuoteMessage,
    PolygonWsTradeMessage,
)
from app.market_data.events.bar import BarEvent
from app.market_data.events.quote import QuoteEvent
from app.market_data.events.trade import TradeEvent
from app.market_data.identity import InstrumentId
from tests.support.provider_contracts.clocks import OBSERVED_AT, observed_clock
from tests.support.provider_contracts.identities import equity_instrument

PROVIDER_SYMBOL = "AAPL"
BAR_TS_MS = 1_704_067_200_000  # 2024-01-01T00:00:00Z


def historical_bar(
    *,
    instrument: InstrumentId | None = None,
    clock: Clock | None = None,
    adjusted: bool = True,
    timestamp_ms: int = BAR_TS_MS,
    request_id: str = "req-contract-1",
) -> BarEvent:
    inst = instrument or equity_instrument()
    clk = clock or observed_clock()
    bar = PolygonAggBar.model_validate(
        {
            "o": "190.1",
            "h": "191.2",
            "l": "189.0",
            "c": "190.5",
            "v": "1000",
            "vw": "190.3",
            "t": timestamp_ms,
            "n": 12,
        }
    )
    response = PolygonAggsResponse.model_validate(
        {
            "status": "OK",
            "request_id": request_id,
            "ticker": PROVIDER_SYMBOL,
            "adjusted": adjusted,
            "results": [bar.model_dump(by_alias=True)],
        }
    )
    return map_bar_event(
        bar,
        response=response,
        instrument=inst,
        currency="USD",
        venue="XNAS",
        timespan="day",
        multiplier=1,
        requested_adjusted=adjusted,
        known_at=OBSERVED_AT,
        clock=clk,
        endpoint_ref="https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2024-01-01/2024-01-02",
        bar_index=0,
        request_symbol=PROVIDER_SYMBOL,
    )


def realtime_trade(
    *,
    instrument: InstrumentId | None = None,
    clock: Clock | None = None,
    trade_id: str = "t-100",
    ts_ms: int = BAR_TS_MS,
) -> TradeEvent:
    msg = PolygonWsTradeMessage.model_validate(
        {"ev": "T", "sym": PROVIDER_SYMBOL, "p": "190.5", "s": "10", "i": trade_id, "t": ts_ms}
    )
    return map_ws_trade(
        msg,
        instrument=instrument or equity_instrument(),
        currency="USD",
        venue="XNAS",
        known_at=OBSERVED_AT,
        clock=clock or observed_clock(),
    )


def realtime_quote(
    *,
    instrument: InstrumentId | None = None,
    clock: Clock | None = None,
    ts_ms: int = BAR_TS_MS,
) -> QuoteEvent:
    msg = PolygonWsQuoteMessage.model_validate(
        {
            "ev": "Q",
            "sym": PROVIDER_SYMBOL,
            "bp": "190.4",
            "bs": "5",
            "ap": "190.6",
            "as": "6",
            "t": ts_ms,
        }
    )
    return map_ws_quote(
        msg,
        instrument=instrument or equity_instrument(),
        currency="USD",
        venue="XNAS",
        known_at=OBSERVED_AT,
        clock=clock or observed_clock(),
    )


def realtime_bar(
    *,
    instrument: InstrumentId | None = None,
    clock: Clock | None = None,
    start_ms: int = BAR_TS_MS,
    end_ms: int | None = None,
) -> BarEvent:
    end = end_ms if end_ms is not None else start_ms + 60_000
    msg = PolygonWsMinuteAggregateMessage.model_validate(
        {
            "ev": "AM",
            "sym": PROVIDER_SYMBOL,
            "v": "100",
            "o": "190.0",
            "h": "191.0",
            "l": "189.5",
            "c": "190.5",
            "vw": "190.2",
            "s": start_ms,
            "e": end,
        }
    )
    return map_ws_minute_bar(
        msg,
        instrument=instrument or equity_instrument(),
        currency="USD",
        venue="XNAS",
        known_at=OBSERVED_AT,
        clock=clock or observed_clock(),
    )
