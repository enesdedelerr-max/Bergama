"""Caller-owned InstrumentId fixtures for provider contract tests."""

from __future__ import annotations

from datetime import UTC, datetime

from app.market_data.enums import AssetClass
from app.market_data.identity import InstrumentId

_EFFECTIVE = datetime(2020, 1, 1, tzinfo=UTC)


def equity_instrument(
    *,
    key: str = "bergama:equity:us:aapl",
    symbol: str = "AAPL",
) -> InstrumentId:
    return InstrumentId(
        instrument_key=key,
        asset_class=AssetClass.EQUITY,
        local_symbol=symbol,
        symbol_effective_from=_EFFECTIVE,
    )


def macro_instrument(
    *,
    key: str = "bergama:macro:us:gdp",
    symbol: str = "GDP",
) -> InstrumentId:
    return InstrumentId(
        instrument_key=key,
        asset_class=AssetClass.MACRO,
        local_symbol=symbol,
        symbol_effective_from=_EFFECTIVE,
    )


def news_anchor_instrument(
    *,
    key: str = "bergama:news:anchor:contract",
) -> InstrumentId:
    """Caller-owned anchor only — connectors must never fabricate this."""
    return InstrumentId(
        instrument_key=key,
        asset_class=AssetClass.OTHER,
        local_symbol=None,
        symbol_effective_from=_EFFECTIVE,
    )
