"""Cross-provider identity contracts (#304E)."""

from __future__ import annotations

import pytest
from app.infrastructure.benzinga.errors import BenzingaMappingFailedError
from tests.support.provider_contracts import benzinga, finnhub, fred, polygon, sec
from tests.support.provider_contracts.assertions import assert_identity_contract
from tests.support.provider_contracts.identities import (
    equity_instrument,
    macro_instrument,
    news_anchor_instrument,
)


@pytest.mark.parametrize(
    ("factory", "caller", "provider_id"),
    [
        (lambda: polygon.historical_bar(), equity_instrument(), polygon.PROVIDER_SYMBOL),
        (lambda: polygon.realtime_trade(), equity_instrument(), polygon.PROVIDER_SYMBOL),
        (lambda: finnhub.reference_event(), equity_instrument(), finnhub.PROVIDER_SYMBOL),
        (lambda: finnhub.fundamental_events()[0], equity_instrument(), finnhub.PROVIDER_SYMBOL),
        (lambda: fred.macro_observation(), macro_instrument(), fred.FRED_SERIES_ID),
        (lambda: sec.filing_events()[0], equity_instrument(), sec.PROVIDER_CIK),
        (lambda: benzinga.news_events()[0], equity_instrument(), "AAPL"),
    ],
)
def test_provider_identifier_never_becomes_canonical_identity(
    factory: object,
    caller: object,
    provider_id: str,
) -> None:
    event = factory()  # type: ignore[operator]
    assert_identity_contract(event, caller_instrument=caller, provider_identifier=provider_id)  # type: ignore[arg-type]
    assert event.source.source_symbol is not None or event.source.source_instrument_id is not None


def test_benzinga_fan_out_and_anchor_fail_closed() -> None:
    mapped = benzinga.news_events(
        stocks=[{"name": "AAPL"}, {"name": "MSFT"}],
        ticker_to_instrument={
            "AAPL": equity_instrument(key="bergama:equity:us:aapl", symbol="AAPL"),
            "MSFT": equity_instrument(key="bergama:equity:us:msft", symbol="MSFT"),
        },
    )
    assert [e.instrument.local_symbol for e in mapped] == ["AAPL", "MSFT"]

    anchored = benzinga.zero_ticker_news()
    assert len(anchored) == 1
    assert anchored[0].instrument == news_anchor_instrument()

    with pytest.raises(BenzingaMappingFailedError, match="anchor_instrument"):
        benzinga.news_events(stocks=[], ticker_to_instrument={}, anchor_instrument=None)
