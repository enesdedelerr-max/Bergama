"""Cross-provider EventEnvelope compatibility contracts (#304E)."""

from __future__ import annotations

import pytest
from tests.support.provider_contracts import benzinga, finnhub, fred, polygon, sec
from tests.support.provider_contracts.assertions import assert_event_envelope_contract


@pytest.mark.parametrize(
    "factory",
    [
        polygon.historical_bar,
        polygon.realtime_trade,
        polygon.realtime_quote,
        polygon.realtime_bar,
        finnhub.reference_event,
        lambda: finnhub.fundamental_events()[0],
        fred.macro_observation,
        lambda: sec.filing_events()[0],
        lambda: benzinga.news_events()[0],
    ],
)
def test_provider_mapped_events_survive_event_envelope_round_trip(factory: object) -> None:
    event = factory()  # type: ignore[operator]
    assert_event_envelope_contract(event)
