"""Cross-provider provenance contracts (#304E)."""

from __future__ import annotations

import pytest
from tests.support.provider_contracts import benzinga, finnhub, fred, polygon, sec
from tests.support.provider_contracts.assertions import assert_provenance_contract


@pytest.mark.parametrize(
    ("factory", "provider"),
    [
        (polygon.historical_bar, "polygon"),
        (polygon.realtime_trade, "polygon"),
        (finnhub.reference_event, "finnhub"),
        (lambda: finnhub.fundamental_events()[0], "finnhub"),
        (fred.macro_observation, "fred"),
        (lambda: sec.filing_events()[0], "sec_edgar"),
        (lambda: benzinga.news_events()[0], "benzinga"),
    ],
)
def test_provenance_provider_literal_and_source_event_id(factory: object, provider: str) -> None:
    event = factory()  # type: ignore[operator]
    assert_provenance_contract(event, provider=provider)


def test_benzinga_preserves_tickers_and_omits_body() -> None:
    event = benzinga.news_events(
        stocks=[{"name": "AAPL"}, {"name": "NVDA"}],
    )[0]
    assert "AAPL" in event.metadata["provider_tickers"]
    assert "NVDA" in event.metadata["provider_tickers"]
    assert "original_id" in event.metadata
    dumped = str(event.model_dump())
    assert "SYNTHETIC_BODY_MUST_NEVER_MAP" not in dumped


def test_sec_preserves_cik_and_accession_in_source() -> None:
    event = sec.filing_events()[0]
    assert event.source.source_instrument_id == "0000320193"
    assert event.accession_number == sec.ACCESSION
    assert "sec_cik" in event.source.extras
