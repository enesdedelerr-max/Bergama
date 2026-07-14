"""Map Polygon realtime WS messages to #301 canonical events."""

from __future__ import annotations

from datetime import datetime

from app.core.clock import Clock
from app.infrastructure.polygon.errors import (
    PolygonMappingFailedError,
    PolygonWebsocketProtocolError,
)
from app.infrastructure.polygon.mapper import decimal_from_provider, ms_to_utc
from app.infrastructure.polygon.ws_schemas import (
    PolygonWsMinuteAggregateMessage,
    PolygonWsQuoteMessage,
    PolygonWsTradeMessage,
)
from app.market_data.enums import AdjustmentState
from app.market_data.events.bar import BarEvent
from app.market_data.events.quote import QuoteEvent
from app.market_data.events.trade import TradeEvent
from app.market_data.identity import InstrumentId
from app.market_data.quality import DataQualityFlags
from app.market_data.serialization import CANONICAL_MARKET_SCHEMA_VERSION
from app.market_data.source import SourceReference

REALTIME_ADJUSTMENT_ASSUMPTION = "unadjusted_live_ws_default"


def _quality_for(*, known_at: datetime, ingested_at: datetime) -> DataQualityFlags:
    if known_at > ingested_at:
        lag_ms = int((known_at - ingested_at).total_seconds() * 1000)
        return DataQualityFlags(is_late=True, late_arrival_lag_ms=max(lag_ms, 0))
    return DataQualityFlags()


def map_ws_trade(
    message: PolygonWsTradeMessage,
    *,
    instrument: InstrumentId,
    currency: str,
    venue: str,
    known_at: datetime,
    clock: Clock,
) -> TradeEvent:
    try:
        occurred = ms_to_utc(message.t)
        ingested_at = clock.now()
        price = decimal_from_provider(message.p, field_name="price")
        size = decimal_from_provider(message.s, field_name="size")
        trade_id = str(message.i) if message.i is not None else None
        extras: dict[str, str] = {
            "endpoint": "stocks.ws",
            "ev": "T",
        }
        if message.x is not None:
            extras["exchange_id"] = str(message.x)
        if message.z is not None:
            extras["tape"] = str(message.z)
        source = SourceReference(
            provider="polygon",
            source_symbol=message.sym,
            source_event_id=trade_id or f"T:{message.sym}:{message.t}",
            extras=extras,
        )
        return TradeEvent(
            schema_version=CANONICAL_MARKET_SCHEMA_VERSION,
            instrument=instrument,
            source=source,
            quality=_quality_for(known_at=known_at, ingested_at=ingested_at),
            adjustment_state=AdjustmentState.UNADJUSTED,
            occurred_at=occurred,
            effective_at=occurred,
            known_at=known_at,
            ingested_at=ingested_at,
            currency=currency,
            venue=venue,
            price=price,
            size=size,
            trade_id=trade_id,
            metadata={},
        )
    except PolygonMappingFailedError:
        raise
    except Exception as exc:
        raise PolygonMappingFailedError("failed to map polygon websocket trade") from exc


def map_ws_quote(
    message: PolygonWsQuoteMessage,
    *,
    instrument: InstrumentId,
    currency: str,
    venue: str,
    known_at: datetime,
    clock: Clock,
) -> QuoteEvent:
    try:
        occurred = ms_to_utc(message.t)
        ingested_at = clock.now()
        bid_price = decimal_from_provider(message.bp, field_name="bid_price")
        ask_price = decimal_from_provider(message.ap, field_name="ask_price")
        bid_size = decimal_from_provider(message.bs, field_name="bid_size")
        ask_size = decimal_from_provider(message.as_, field_name="ask_size")
        extras: dict[str, str] = {
            "endpoint": "stocks.ws",
            "ev": "Q",
        }
        if message.bx is not None:
            extras["bid_exchange_id"] = str(message.bx)
        if message.ax is not None:
            extras["ask_exchange_id"] = str(message.ax)
        source = SourceReference(
            provider="polygon",
            source_symbol=message.sym,
            source_event_id=f"Q:{message.sym}:{message.t}",
            extras=extras,
        )
        return QuoteEvent(
            schema_version=CANONICAL_MARKET_SCHEMA_VERSION,
            instrument=instrument,
            source=source,
            quality=_quality_for(known_at=known_at, ingested_at=ingested_at),
            adjustment_state=AdjustmentState.UNADJUSTED,
            occurred_at=occurred,
            effective_at=occurred,
            known_at=known_at,
            ingested_at=ingested_at,
            currency=currency,
            venue=venue,
            bid_price=bid_price,
            ask_price=ask_price,
            bid_size=bid_size,
            ask_size=ask_size,
            metadata={},
        )
    except PolygonMappingFailedError:
        raise
    except Exception as exc:
        raise PolygonMappingFailedError("failed to map polygon websocket quote") from exc


def map_ws_minute_bar(
    message: PolygonWsMinuteAggregateMessage,
    *,
    instrument: InstrumentId,
    currency: str,
    venue: str,
    known_at: datetime,
    clock: Clock,
) -> BarEvent:
    try:
        if message.ev != "AM":
            raise PolygonWebsocketProtocolError("only AM minute aggregates are mapped")
        window_start = ms_to_utc(message.s)
        window_end = ms_to_utc(message.e)
        if window_end < window_start:
            raise PolygonMappingFailedError("AM window_end must be >= window_start")
        close_time = window_end
        ingested_at = clock.now()
        open_ = decimal_from_provider(message.o, field_name="open")
        high = decimal_from_provider(message.h, field_name="high")
        low = decimal_from_provider(message.low, field_name="low")
        close = decimal_from_provider(message.c, field_name="close")
        volume = decimal_from_provider(message.v, field_name="volume")
        vwap = (
            decimal_from_provider(message.vw, field_name="vwap") if message.vw is not None else None
        )
        source = SourceReference(
            provider="polygon",
            source_symbol=message.sym,
            source_event_id=f"AM:{message.sym}:{message.s}:{message.e}",
            extras={
                "endpoint": "stocks.ws",
                "ev": "AM",
                "adjustment_assumption": REALTIME_ADJUSTMENT_ASSUMPTION,
                "provider_window_start_ms": str(message.s),
                "provider_window_end_ms": str(message.e),
            },
        )
        return BarEvent(
            schema_version=CANONICAL_MARKET_SCHEMA_VERSION,
            instrument=instrument,
            source=source,
            quality=_quality_for(known_at=known_at, ingested_at=ingested_at),
            adjustment_state=AdjustmentState.UNADJUSTED,
            occurred_at=close_time,
            effective_at=window_start,
            known_at=known_at,
            ingested_at=ingested_at,
            currency=currency,
            venue=venue,
            window_start=window_start,
            window_end=window_end,
            close_time=close_time,
            open=open_,
            high=high,
            low=low,
            close=close,
            volume=volume,
            vwap=vwap,
            metadata={},
        )
    except (PolygonMappingFailedError, PolygonWebsocketProtocolError):
        raise
    except Exception as exc:
        raise PolygonMappingFailedError("failed to map polygon websocket minute bar") from exc
