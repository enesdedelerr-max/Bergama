"""Integration boundary tests for Human Review ↔ Dashboard."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from app.dashboard.engine import assemble_dashboard_from_parts
from app.dashboard.policy import POLICY_VERSION_V1 as DASHBOARD_POLICY_VERSION_V1
from app.human_review.engine import assemble_human_review_from_parts
from app.human_review.policy import POLICY_VERSION_V1
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
ATTESTATION = "recorded-human-authority-v1"


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


def test_human_review_consumes_dashboard_without_mutating_upstream() -> None:
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
    review = assemble_human_review_from_parts(
        dashboard=dashboard, as_of=AS_OF, attestation=ATTESTATION
    )

    assert review.policy_version_id == POLICY_VERSION_V1
    assert dashboard.policy_version_id == DASHBOARD_POLICY_VERSION_V1
    assert len(review.records) == len(dashboard.records)
    for review_record, dashboard_record in zip(review.records, dashboard.records, strict=True):
        assert review_record.score_record_id == dashboard_record.score_record_id
        assert review_record.score == dashboard_record.score
        assert review_record.instrument_key == dashboard_record.instrument_key
        assert review_record.local_symbol == dashboard_record.local_symbol
        assert review_record.components == dashboard_record.components
    assert review.dashboard_output_id == dashboard.dashboard_output_id
    assert review.provenance.upstream_dashboard_output_id == dashboard.dashboard_output_id
    assert review.provenance.upstream_dashboard_config_fingerprint == (
        dashboard.provenance.config_fingerprint
    )
    assert review.provenance.upstream_dashboard_input_fingerprint == (
        dashboard.provenance.input_fingerprint
    )
    assert review.human_review_output_id != dashboard.dashboard_output_id
    assert review.attestation.recorded_payload == ATTESTATION
    assert review.history.human_review_output_id == review.human_review_output_id


def test_human_review_package_has_no_direct_scoring_or_briefing_imports() -> None:
    root = Path(__file__).resolve().parents[2] / "app" / "human_review"
    forbidden = (
        "app.premarket.scoring",
        "app.premarket.morning_briefing",
        "app.features.",
    )
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{path.name} contains forbidden import {token}"
