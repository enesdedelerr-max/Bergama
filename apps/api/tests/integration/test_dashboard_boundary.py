"""Integration boundary tests for Dashboard ↔ Morning Briefing."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from app.dashboard.engine import assemble_dashboard_from_parts
from app.dashboard.policy import POLICY_VERSION_V1
from app.premarket.gap.engine import scan_gaps_from_parts
from app.premarket.morning_briefing import assemble_briefing_from_parts
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


def test_dashboard_consumes_briefing_without_mutating_upstream() -> None:
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
    dashboard = assemble_dashboard_from_parts(briefing=briefing, as_of=AS_OF)

    assert dashboard.policy_version_id == POLICY_VERSION_V1
    assert len(dashboard.records) == len(briefing.records)
    for dashboard_record, briefing_record in zip(dashboard.records, briefing.records, strict=True):
        assert dashboard_record.score_record_id == briefing_record.score_record_id
        assert dashboard_record.score == briefing_record.score
        assert dashboard_record.instrument_key == briefing_record.instrument_key
        assert dashboard_record.local_symbol == briefing_record.local_symbol
        assert dashboard_record.components == briefing_record.components
    assert dashboard.provenance.upstream_briefing_id == briefing.briefing_id
    assert dashboard.provenance.upstream_briefing_config_fingerprint == (
        briefing.provenance.config_fingerprint
    )
    assert dashboard.provenance.upstream_briefing_input_fingerprint == (
        briefing.provenance.input_fingerprint
    )
    assert dashboard.dashboard_output_id != briefing.briefing_id


def test_dashboard_package_has_no_direct_scoring_or_private_briefing_imports() -> None:
    root = Path(__file__).resolve().parents[2] / "app" / "dashboard"
    forbidden = (
        "app.premarket.scoring",
        "app.premarket.morning_briefing.models",
        "app.premarket.morning_briefing.engine",
        "app.premarket.morning_briefing.pipeline",
        "app.premarket.morning_briefing.identity",
        "app.premarket.morning_briefing.provenance",
        "app.premarket.morning_briefing.validate_",
        "app.premarket.morning_briefing.ordering",
        "app.premarket.morning_briefing.output",
    )
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{path.name} contains forbidden import {token}"
