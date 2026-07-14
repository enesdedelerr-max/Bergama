"""Canonical market-data enumerations."""

from __future__ import annotations

from enum import StrEnum


class AssetClass(StrEnum):
    """Provider-independent asset class."""

    EQUITY = "equity"
    ETF = "etf"
    OPTION = "option"
    FUTURE = "future"
    FOREX = "forex"
    CRYPTO = "crypto"
    INDEX = "index"
    FIXED_INCOME = "fixed_income"
    MACRO = "macro"
    OTHER = "other"


class MarketEventType(StrEnum):
    """Discriminating event type for CanonicalMarketEvent."""

    QUOTE = "quote"
    TRADE = "trade"
    BAR = "bar"
    REFERENCE_DATA = "reference_data"
    FUNDAMENTAL = "fundamental"
    MACRO = "macro"
    FILING = "filing"
    NEWS = "news"


class AdjustmentState(StrEnum):
    """Corporate-action adjustment declaration for price/size series."""

    UNADJUSTED = "unadjusted"
    SPLIT_ADJUSTED = "split_adjusted"
    DIVIDEND_ADJUSTED = "dividend_adjusted"
    SPLIT_AND_DIVIDEND_ADJUSTED = "split_and_dividend_adjusted"
    UNKNOWN = "unknown"
