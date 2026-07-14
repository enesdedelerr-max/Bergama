"""Shared synthetic CanonicalMarketEvent builders for orchestrator tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.market_data.enums import AdjustmentState, AssetClass, MarketEventType
from app.market_data.events.bar import BarEvent
from app.market_data.events.quote import QuoteEvent
from app.market_data.events.trade import TradeEvent
from app.market_data.identity import InstrumentId
from app.market_data.quality import DataQualityFlags
from app.market_data.serialization import CANONICAL_MARKET_SCHEMA_VERSION
from app.market_data.source import SourceReference

_T0 = datetime(2024, 1, 1, 15, 0, 0, tzinfo=UTC)
EVENT_TIME = _T0


def equity(key: str = "bergama:equity:us:aapl", symbol: str = "AAPL") -> InstrumentId:
    return InstrumentId(
        instrument_key=key,
        asset_class=AssetClass.EQUITY,
        local_symbol=symbol,
        symbol_effective_from=datetime(2020, 1, 1, tzinfo=UTC),
    )


def trade_event(
    *,
    source_event_id: str = "t-1",
    occurred_at: datetime | None = None,
    instrument: InstrumentId | None = None,
    price: str = "190.50",
    size: str = "10",
    quality: DataQualityFlags | None = None,
    trade_id: str | None = "trd-1",
) -> TradeEvent:
    ts = occurred_at or _T0
    return TradeEvent(
        schema_version=CANONICAL_MARKET_SCHEMA_VERSION,
        instrument=instrument or equity(),
        source=SourceReference(
            provider="polygon",
            source_symbol="AAPL",
            source_event_id=source_event_id,
        ),
        quality=quality or DataQualityFlags(),
        adjustment_state=AdjustmentState.UNADJUSTED,
        occurred_at=ts,
        effective_at=ts,
        known_at=ts,
        ingested_at=ts + timedelta(seconds=1),
        currency="USD",
        venue="XNAS",
        price=Decimal(price),
        size=Decimal(size),
        trade_id=trade_id,
    )


def quote_event(
    *,
    source_event_id: str = "q-1",
    occurred_at: datetime | None = None,
    instrument: InstrumentId | None = None,
) -> QuoteEvent:
    ts = occurred_at or _T0
    return QuoteEvent(
        schema_version=CANONICAL_MARKET_SCHEMA_VERSION,
        instrument=instrument or equity(),
        source=SourceReference(
            provider="polygon",
            source_symbol="AAPL",
            source_event_id=source_event_id,
        ),
        quality=DataQualityFlags(),
        adjustment_state=AdjustmentState.UNADJUSTED,
        occurred_at=ts,
        effective_at=ts,
        known_at=ts,
        ingested_at=ts + timedelta(seconds=1),
        currency="USD",
        venue="XNAS",
        bid_price=Decimal("190.00"),
        ask_price=Decimal("190.10"),
        bid_size=Decimal("100"),
        ask_size=Decimal("200"),
    )


def bar_event(
    *,
    source_event_id: str = "b-1",
    occurred_at: datetime | None = None,
    instrument: InstrumentId | None = None,
) -> BarEvent:
    ts = occurred_at or _T0
    close_time = ts
    window_start = ts - timedelta(minutes=1)
    return BarEvent(
        schema_version=CANONICAL_MARKET_SCHEMA_VERSION,
        instrument=instrument or equity(),
        source=SourceReference(
            provider="polygon",
            source_symbol="AAPL",
            source_event_id=source_event_id,
        ),
        quality=DataQualityFlags(),
        adjustment_state=AdjustmentState.SPLIT_ADJUSTED,
        occurred_at=close_time,
        effective_at=close_time,
        known_at=close_time,
        ingested_at=close_time + timedelta(seconds=1),
        currency="USD",
        venue="XNAS",
        window_start=window_start,
        window_end=close_time,
        close_time=close_time,
        open=Decimal("190.0"),
        high=Decimal("191.0"),
        low=Decimal("189.0"),
        close=Decimal("190.5"),
        volume=Decimal("1000"),
    )


def pit_invalid_trade() -> TradeEvent:
    """Construct via model_construct to bypass validators for PIT rejection tests."""
    ts = _T0
    later = ts + timedelta(hours=1)
    return TradeEvent.model_construct(
        event_type=MarketEventType.TRADE,
        schema_version=CANONICAL_MARKET_SCHEMA_VERSION,
        instrument=equity(),
        source=SourceReference(
            provider="polygon",
            source_symbol="AAPL",
            source_event_id="bad-pit",
        ),
        quality=DataQualityFlags(),
        adjustment_state=AdjustmentState.UNADJUSTED,
        occurred_at=later,
        effective_at=later,
        known_at=ts,
        ingested_at=ts,
        currency="USD",
        venue="XNAS",
        price=Decimal("190.50"),
        size=Decimal("10"),
        trade_id="bad",
        aggressor_side=None,
        metadata={},
    )


def revision_trade(*, of_source_id: str = "t-1") -> TradeEvent:
    ts = _T0 + timedelta(minutes=5)
    return TradeEvent(
        schema_version=CANONICAL_MARKET_SCHEMA_VERSION,
        instrument=equity(),
        source=SourceReference(
            provider="polygon",
            source_symbol="AAPL",
            source_event_id=of_source_id,
        ),
        quality=DataQualityFlags(is_revision=True, revision_of_event_id="orig-id"),
        adjustment_state=AdjustmentState.UNADJUSTED,
        occurred_at=ts,
        effective_at=ts,
        known_at=ts,
        ingested_at=ts + timedelta(seconds=1),
        currency="USD",
        venue="XNAS",
        price=Decimal("191.00"),
        size=Decimal("10"),
        trade_id="trd-rev",
    )
