"""Cross-provider PIT / time contracts (#304E)."""

from __future__ import annotations

import pytest
from app.infrastructure.fred.errors import FredMappingFailedError
from app.infrastructure.polygon.errors import PolygonMappingFailedError
from tests.support.provider_contracts import benzinga, finnhub, fred, polygon, sec
from tests.support.provider_contracts.assertions import assert_pit_contract
from tests.support.provider_contracts.clocks import OBSERVED_AT


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
def test_all_provider_events_obey_pit_contract(factory: object) -> None:
    event = factory()  # type: ignore[operator]
    assert_pit_contract(event)
    assert event.known_at <= OBSERVED_AT or event.quality.is_late


def test_finnhub_same_response_shares_observation_clock() -> None:
    events = finnhub.fundamental_events()
    assert len(events) >= 2
    stamps = {(e.occurred_at, e.effective_at, e.known_at, e.ingested_at) for e in events}
    assert len(stamps) == 1


def test_fred_missing_dot_is_not_zero() -> None:
    assert fred.missing_observation() is None


def test_fred_invalid_vintage_ordering_fails_closed() -> None:
    with pytest.raises(FredMappingFailedError, match="occurred_at > known_at"):
        fred.macro_observation(obs_date="2024-06-01", realtime_start="2024-01-01")


def test_sec_amendment_remains_distinct_form() -> None:
    base = sec.filing_events(form="10-K")[0]
    amended = sec.filing_events(form="10-K/A", accession="0000320193-24-000002")[0]
    assert base.form_type == "10-K"
    assert amended.form_type == "10-K/A"
    assert amended.metadata.get("is_amendment") == "true"


def test_benzinga_created_and_updated_semantics() -> None:
    event = benzinga.news_events()[0]
    assert event.occurred_at == event.effective_at
    assert event.known_at == event.ingested_at == OBSERVED_AT
    assert "updated_at" in event.metadata
    assert event.quality.revision_of_event_id is None


def test_polygon_invalid_timestamp_fails_closed() -> None:
    with pytest.raises(PolygonMappingFailedError):
        polygon.historical_bar(timestamp_ms=-(10**20))
