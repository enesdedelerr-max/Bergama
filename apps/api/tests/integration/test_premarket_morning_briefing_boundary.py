"""Integration boundary tests for Morning Briefing ↔ Premarket Scoring."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.premarket.gap.engine import scan_gaps_from_parts
from app.premarket.morning_briefing.engine import assemble_briefing_from_parts
from app.premarket.morning_briefing.policy import POLICY_VERSION_V1
from app.premarket.scoring.engine import scan_scores_from_parts
from app.premarket.scoring.models import ScoreConfig
from app.premarket.watchlist.engine import generate_watchlist
from app.premarket.watchlist.models import (
    WatchlistCandidate,
    WatchlistConfig,
    WatchlistGenerationRequest,
    WatchlistInclusionRule,
)
from tests.support.market_data_fixtures import instrument, make_bar, source

AS_OF = datetime(2026, 7, 17, 14, 0, tzinfo=UTC)
DAY1 = datetime(2026, 7, 15, 20, 0, tzinfo=UTC)
DAY2 = datetime(2026, 7, 16, 20, 0, tzinfo=UTC)


def _bar(
    instrument_key: str,
    symbol: str,
    close_time: datetime,
    open_p: str,
    close_p: str,
    sid: str,
):
    known = close_time + timedelta(minutes=1)
    return make_bar(
        instrument=instrument(instrument_key=instrument_key, local_symbol=symbol),
        source=source(provider="fixture", source_event_id=sid),
        occurred_at=close_time,
        effective_at=close_time,
        known_at=known,
        ingested_at=known + timedelta(seconds=1),
        window_start=close_time - timedelta(hours=24),
        window_end=close_time,
        close_time=close_time,
        open=Decimal(open_p),
        high=Decimal(close_p) + Decimal("1"),
        low=Decimal(open_p) - Decimal("1"),
        close=Decimal(close_p),
        volume=Decimal("1000"),
    )


def test_briefing_consumes_scoring_without_mutating_scores() -> None:
    watchlist = generate_watchlist(
        WatchlistGenerationRequest(
            candidates=(
                WatchlistCandidate(instrument_key="bergama:equity:us:aapl", local_symbol="AAPL"),
                WatchlistCandidate(instrument_key="bergama:equity:us:msft", local_symbol="MSFT"),
            ),
            as_of=AS_OF,
            config=WatchlistConfig(
                rules=(
                    WatchlistInclusionRule(
                        rule_id="core",
                        rule_priority=1,
                        inclusion_reason="approved",
                        allowed_instrument_keys=(
                            "bergama:equity:us:aapl",
                            "bergama:equity:us:msft",
                        ),
                    ),
                )
            ),
        )
    )
    bars = (
        _bar("bergama:equity:us:aapl", "AAPL", DAY1, "100", "100", "a1"),
        _bar("bergama:equity:us:aapl", "AAPL", DAY2, "110", "111", "a2"),
        _bar("bergama:equity:us:msft", "MSFT", DAY1, "50", "50", "m1"),
        _bar("bergama:equity:us:msft", "MSFT", DAY2, "55", "56", "m2"),
    )
    gaps = scan_gaps_from_parts(watchlist=watchlist, bars=bars, as_of=AS_OF)
    scores = scan_scores_from_parts(
        watchlist=watchlist,
        as_of=AS_OF,
        config=ScoreConfig(),
        gaps=gaps,
    )
    briefing = assemble_briefing_from_parts(scores=scores, as_of=AS_OF)

    assert briefing.policy_version_id == POLICY_VERSION_V1
    assert len(briefing.records) == len(scores.records)
    for briefing_record, score_record in zip(briefing.records, scores.records, strict=True):
        assert briefing_record.score_record_id == score_record.score_record_id
        assert briefing_record.score == score_record.score
        assert briefing_record.instrument_key == score_record.instrument_key
    assert briefing.provenance.upstream_scoring_config_fingerprint == (
        scores.provenance.config_fingerprint
    )
    assert briefing.provenance.upstream_scoring_input_fingerprint == (
        scores.provenance.input_fingerprint
    )
