"""Canonical market-data contracts (Sprint 3 Issue #301).

Provider-independent, point-in-time-safe domain models. No connectors,
Kafka publishing, Iceberg writers, or strategy logic live here.
"""

from __future__ import annotations

from app.market_data.enums import (
    AdjustmentState,
    AssetClass,
    MarketEventType,
)
from app.market_data.envelope import CanonicalMarketEvent, parse_canonical_market_event
from app.market_data.events.bar import BarEvent
from app.market_data.events.filing import FilingEvent
from app.market_data.events.fundamental import FundamentalEvent
from app.market_data.events.macro import MacroEvent
from app.market_data.events.news import NewsEvent
from app.market_data.events.quote import QuoteEvent
from app.market_data.events.reference import ReferenceDataEvent
from app.market_data.events.trade import TradeEvent
from app.market_data.identity import InstrumentId
from app.market_data.keys import build_deduplication_key, build_idempotency_key
from app.market_data.quality import DataQualityFlags
from app.market_data.serialization import (
    CANONICAL_MARKET_SCHEMA_VERSION,
    market_event_to_envelope,
    market_event_to_payload,
)
from app.market_data.source import SourceReference

__all__ = [
    "CANONICAL_MARKET_SCHEMA_VERSION",
    "AdjustmentState",
    "AssetClass",
    "BarEvent",
    "CanonicalMarketEvent",
    "DataQualityFlags",
    "FilingEvent",
    "FundamentalEvent",
    "InstrumentId",
    "MacroEvent",
    "MarketEventType",
    "NewsEvent",
    "QuoteEvent",
    "ReferenceDataEvent",
    "SourceReference",
    "TradeEvent",
    "build_deduplication_key",
    "build_idempotency_key",
    "market_event_to_envelope",
    "market_event_to_payload",
    "parse_canonical_market_event",
]
