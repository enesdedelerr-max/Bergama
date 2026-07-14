"""Synthetic Finnhub fixtures mapped to canonical events."""

from __future__ import annotations

from datetime import datetime

from app.infrastructure.finnhub.mapper import map_fundamental_events, map_reference_event
from app.infrastructure.finnhub.schemas import FinnhubBasicFinancials, FinnhubCompanyProfile2
from app.market_data.events.fundamental import FundamentalEvent
from app.market_data.events.reference import ReferenceDataEvent
from app.market_data.identity import InstrumentId
from tests.support.provider_contracts.clocks import OBSERVED_AT
from tests.support.provider_contracts.identities import equity_instrument

PROVIDER_SYMBOL = "AAPL"


def reference_event(
    *,
    instrument: InstrumentId | None = None,
    observed_at: datetime | None = None,
    symbol: str = PROVIDER_SYMBOL,
) -> ReferenceDataEvent:
    profile = FinnhubCompanyProfile2.model_validate(
        {
            "country": "US",
            "currency": "USD",
            "exchange": "NASDAQ",
            "name": "Synthetic Apple Fixture",
            "ticker": symbol,
            "ipo": "1980-12-12",
            "finnhubIndustry": "Technology",
        }
    )
    return map_reference_event(
        profile,
        instrument=instrument or equity_instrument(),
        symbol=symbol,
        observed_at=observed_at or OBSERVED_AT,
        request_id="fh-req-1",
        caller_currency="USD",
    )


def fundamental_events(
    *,
    instrument: InstrumentId | None = None,
    observed_at: datetime | None = None,
    symbol: str = PROVIDER_SYMBOL,
    pe_ttm: str = "28.5",
) -> tuple[FundamentalEvent, ...]:
    payload = FinnhubBasicFinancials.model_validate(
        {
            "symbol": symbol,
            "metric": {
                "peTTM": pe_ttm,
                "roeTTM": "45.1",
            },
        }
    )
    return map_fundamental_events(
        payload,
        instrument=instrument or equity_instrument(),
        symbol=symbol,
        observed_at=observed_at or OBSERVED_AT,
        request_id="fh-req-2",
        caller_currency="USD",
    )
