"""Shared fixtures for canonical market-data tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from app.market_data.enums import AdjustmentState, AssetClass
from app.market_data.events.bar import BarEvent
from app.market_data.events.filing import FilingEvent
from app.market_data.events.fundamental import FundamentalEvent
from app.market_data.events.macro import MacroEvent
from app.market_data.events.news import NewsEvent
from app.market_data.events.quote import QuoteEvent
from app.market_data.events.reference import ReferenceDataEvent
from app.market_data.events.trade import TradeEvent
from app.market_data.identity import InstrumentId
from app.market_data.quality import DataQualityFlags
from app.market_data.serialization import CANONICAL_MARKET_SCHEMA_VERSION
from app.market_data.source import SourceReference

T0 = datetime(2026, 7, 13, 14, 30, 0, tzinfo=UTC)


def instrument(**overrides: Any) -> InstrumentId:
    data: dict[str, Any] = {
        "instrument_key": "bergama:equity:us:aapl",
        "asset_class": AssetClass.EQUITY,
        "local_symbol": "AAPL",
        "symbol_effective_from": datetime(2020, 1, 1, tzinfo=UTC),
        "symbol_effective_to": None,
    }
    data.update(overrides)
    return InstrumentId.model_validate(data)


def source(**overrides: Any) -> SourceReference:
    data: dict[str, Any] = {
        "provider": "polygon",
        "source_symbol": "AAPL",
        "source_instrument_id": "P-AAPL",
        "source_event_id": "evt-1",
        "source_payload_ref": "s3://raw/polygon/evt-1.json",
        "extras": {"feed": "stocks"},
    }
    data.update(overrides)
    return SourceReference.model_validate(data)


def pit(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "occurred_at": T0,
        "effective_at": T0,
        "known_at": T0 + timedelta(milliseconds=50),
        "ingested_at": T0 + timedelta(milliseconds=100),
    }
    data.update(overrides)
    return data


def base_kwargs(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "schema_version": CANONICAL_MARKET_SCHEMA_VERSION,
        "instrument": instrument(),
        "source": source(),
        "quality": DataQualityFlags(),
        "adjustment_state": AdjustmentState.UNADJUSTED,
        "currency": "USD",
        "venue": "XNAS",
        "metadata": {},
        **pit(),
    }
    data.update(overrides)
    return data


def make_quote(**overrides: Any) -> QuoteEvent:
    data = base_kwargs(
        bid_price=Decimal("190.10"),
        ask_price=Decimal("190.15"),
        bid_size=Decimal("100"),
        ask_size=Decimal("200"),
    )
    data.update(overrides)
    return QuoteEvent.model_validate(data)


def make_trade(**overrides: Any) -> TradeEvent:
    data = base_kwargs(
        price=Decimal("190.12"),
        size=Decimal("50"),
        trade_id="T-1",
        aggressor_side="buy",
    )
    data.update(overrides)
    return TradeEvent.model_validate(data)


def make_bar(**overrides: Any) -> BarEvent:
    close = T0
    data = base_kwargs(
        occurred_at=close,
        window_start=close - timedelta(minutes=1),
        window_end=close,
        close_time=close,
        open=Decimal("190.00"),
        high=Decimal("190.50"),
        low=Decimal("189.80"),
        close=Decimal("190.20"),
        volume=Decimal("10000"),
        vwap=Decimal("190.10"),
        trade_count=42,
    )
    data.update(overrides)
    return BarEvent.model_validate(data)


def make_reference(**overrides: Any) -> ReferenceDataEvent:
    data = base_kwargs(
        currency=None,
        venue=None,
        name="Apple Inc",
        exchange_mic="XNAS",
        isin="US0378331005",
        status="active",
    )
    data.update(overrides)
    return ReferenceDataEvent.model_validate(data)


def make_fundamental(**overrides: Any) -> FundamentalEvent:
    data = base_kwargs(
        venue=None,
        metric_code="eps_basic",
        period="2025-Q4",
        value=Decimal("1.25"),
        unit="currency",
    )
    data.update(overrides)
    return FundamentalEvent.model_validate(data)


def make_macro(**overrides: Any) -> MacroEvent:
    data = base_kwargs(
        instrument=instrument(
            instrument_key="bergama:macro:us:gdp",
            asset_class=AssetClass.MACRO,
            local_symbol="GDP",
        ),
        currency=None,
        venue=None,
        series_id="GDP",
        value=Decimal("2.1"),
        unit="percent",
        frequency="quarterly",
    )
    data.update(overrides)
    return MacroEvent.model_validate(data)


def make_filing(**overrides: Any) -> FilingEvent:
    data = base_kwargs(
        currency=None,
        venue=None,
        form_type="10-K",
        accession_number="0000320193-26-000001",
        title="Annual report",
        document_ref="edgar://0000320193-26-000001",
    )
    data.update(overrides)
    return FilingEvent.model_validate(data)


def make_news(**overrides: Any) -> NewsEvent:
    data = base_kwargs(
        currency=None,
        venue=None,
        headline="Apple announces product event",
        summary="Details TBD",
        url_ref="https://example.invalid/news/1",
        language="en",
        topics=("tech", "earnings"),
    )
    data.update(overrides)
    return NewsEvent.model_validate(data)
