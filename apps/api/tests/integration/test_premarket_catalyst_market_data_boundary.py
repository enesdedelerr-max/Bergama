"""Integration boundary tests for Premarket Catalyst ↔ Market Data NewsEvent."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.premarket.catalyst.engine import normalize_catalysts_from_parts
from app.premarket.catalyst.models import CatalystClassificationRule, CatalystConfig
from tests.support.market_data_fixtures import instrument, make_news, source

AS_OF = datetime(2026, 7, 17, 13, 0, tzinfo=UTC)
T0 = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def test_catalyst_consumes_canonical_news_event_without_contract_changes() -> None:
    aapl = make_news(
        headline="AAPL earnings",
        topics=("earnings",),
        instrument=instrument(instrument_key="bergama:equity:us:aapl", local_symbol="AAPL"),
        source=source(provider="fixture", source_event_id="md-aapl-1"),
        occurred_at=T0,
        effective_at=T0,
        known_at=T0 + timedelta(minutes=1),
        ingested_at=T0 + timedelta(minutes=2),
    )
    msft = make_news(
        headline="MSFT product",
        topics=("product",),
        instrument=instrument(instrument_key="bergama:equity:us:msft", local_symbol="MSFT"),
        source=source(provider="fixture", source_event_id="md-msft-1"),
        occurred_at=T0 + timedelta(minutes=2),
        effective_at=T0 + timedelta(minutes=2),
        known_at=T0 + timedelta(minutes=3),
        ingested_at=T0 + timedelta(minutes=4),
    )

    # Importing/using NewsEvent fields must not require mutating Market Data.
    assert aapl.event_type.value == "news"
    assert aapl.instrument.instrument_key == "bergama:equity:us:aapl"

    result = normalize_catalysts_from_parts(
        events=(msft, aapl),
        as_of=AS_OF,
        config=CatalystConfig(
            classification_rules=(
                CatalystClassificationRule(
                    rule_id="earnings",
                    rule_priority=10,
                    catalyst_type="earnings",
                    match_topics=("earnings",),
                ),
                CatalystClassificationRule(
                    rule_id="product",
                    rule_priority=20,
                    catalyst_type="product",
                    match_topics=("product",),
                ),
            )
        ),
    )
    assert [record.instrument_key for record in result.records] == [
        "bergama:equity:us:aapl",
        "bergama:equity:us:msft",
    ]
    assert result.records[0].catalyst_type == "earnings"
    assert result.records[1].catalyst_type == "product"
    assert result.records[0].local_symbol == "AAPL"
    assert result.records[1].local_symbol == "MSFT"
