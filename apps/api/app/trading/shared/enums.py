"""Shared trading enumerations."""

from __future__ import annotations

from enum import StrEnum


class EngineType(StrEnum):
    """Canonical trading-horizon engine identifiers."""

    DAY_TRADING = "day_trading"
    SWING = "swing"
    INVESTING = "investing"
    OPTIONS = "options"
    FUTURES = "futures"
    CRYPTO = "crypto"


class SupportedAssetClass(StrEnum):
    """Asset classes an engine may declare support for."""

    EQUITY = "equity"
    ETF = "etf"
    OPTION = "option"
    FUTURE = "future"
    CRYPTO = "crypto"
    FOREX = "forex"
    FIXED_INCOME = "fixed_income"


class SupportedTimeframe(StrEnum):
    """Canonical timeframe labels for engine capability declarations."""

    TICK = "tick"
    SECOND_1 = "1s"
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    HOUR_1 = "1h"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"
