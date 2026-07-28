"""Integration boundary tests for Premarket Watchlist ↔ Market Data identity."""

from __future__ import annotations

from datetime import UTC, datetime

from app.premarket.watchlist.engine import generate_watchlist_from_parts
from app.premarket.watchlist.models import WatchlistConfig, WatchlistInclusionRule
from app.premarket.watchlist.normalize import normalize_candidate
from tests.support.market_data_fixtures import instrument


def test_watchlist_consumes_canonical_instrument_id_without_contract_changes() -> None:
    aapl = instrument(instrument_key="bergama:equity:us:aapl", local_symbol="AAPL")
    msft = instrument(instrument_key="bergama:equity:us:msft", local_symbol="MSFT")
    ignored = instrument(instrument_key="bergama:equity:us:tsla", local_symbol="TSLA")

    normalized = normalize_candidate(aapl)
    assert normalized.instrument_key == aapl.instrument_key
    assert normalized.local_symbol == "AAPL"

    result = generate_watchlist_from_parts(
        candidates=(msft, aapl, ignored),
        as_of=datetime(2026, 7, 17, 13, 0, tzinfo=UTC),
        config=WatchlistConfig(
            rules=(
                WatchlistInclusionRule(
                    rule_id="equity-core",
                    rule_priority=5,
                    inclusion_reason="approved_equity_core",
                    allowed_instrument_keys=(
                        "bergama:equity:us:aapl",
                        "bergama:equity:us:msft",
                    ),
                ),
            )
        ),
    )
    assert [entry.instrument_key for entry in result.entries] == [
        "bergama:equity:us:aapl",
        "bergama:equity:us:msft",
    ]
    assert result.entries[0].local_symbol == "AAPL"
    assert result.entries[1].local_symbol == "MSFT"
