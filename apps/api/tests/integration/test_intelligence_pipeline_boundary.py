"""Integration boundary tests for Intelligence Pipeline Core (Issue #126)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from app.dashboard.models import DashboardConfig
from app.intelligence_pipeline import (
    PipelineOutcome,
    PipelineRequest,
    run_intelligence_pipeline,
)
from app.premarket.catalyst.models import CatalystClassificationRule, CatalystConfig
from app.premarket.gap.models import GapConfig
from app.premarket.morning_briefing.models import BriefingConfig
from app.premarket.scoring.models import ScoreConfig
from app.premarket.watchlist.models import (
    WatchlistCandidate,
    WatchlistConfig,
    WatchlistInclusionRule,
)
from tests.support.market_data_fixtures import instrument, make_bar, make_news, source

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


def _request(**overrides: Any) -> PipelineRequest:
    payload: dict[str, Any] = {
        "as_of": AS_OF,
        "candidates": (
            WatchlistCandidate(instrument_key="bergama:equity:us:aapl", local_symbol="AAPL"),
            WatchlistCandidate(instrument_key="bergama:equity:us:msft", local_symbol="MSFT"),
        ),
        "watchlist_config": WatchlistConfig(
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
        "bars": (
            _bar("bergama:equity:us:aapl", "AAPL", DAY1, "100", "100", "a1"),
            _bar("bergama:equity:us:aapl", "AAPL", DAY2, "110", "111", "a2"),
            _bar("bergama:equity:us:msft", "MSFT", DAY1, "50", "50", "m1"),
            _bar("bergama:equity:us:msft", "MSFT", DAY2, "55", "56", "m2"),
        ),
        "gap_config": GapConfig(),
        "events": (
            make_news(
                headline="Apple earnings preview",
                summary="Quarterly results expected",
                url_ref="https://example.invalid/news/aapl-1",
                topics=("earnings", "tech"),
                occurred_at=AS_OF - timedelta(hours=2),
                effective_at=AS_OF - timedelta(hours=2),
                known_at=AS_OF - timedelta(hours=1),
                ingested_at=AS_OF - timedelta(minutes=30),
                source=source(provider="fixture", source_event_id="news-1"),
                instrument=instrument(instrument_key="bergama:equity:us:aapl", local_symbol="AAPL"),
            ),
        ),
        "catalyst_config": CatalystConfig(
            classification_rules=(
                CatalystClassificationRule(
                    rule_id="earnings-topic",
                    rule_priority=10,
                    catalyst_type="earnings",
                    match_topics=("earnings",),
                ),
            )
        ),
        "score_config": ScoreConfig(),
        "briefing_config": BriefingConfig(),
        "dashboard_config": DashboardConfig(),
    }
    payload.update(overrides)
    return PipelineRequest(**payload)


def test_i01_full_valid_core_path_through_public_stages() -> None:
    result = run_intelligence_pipeline(_request())
    assert result.outcome == PipelineOutcome.COMPLETED_DASHBOARD
    assert result.watchlist is not None
    assert len(result.watchlist.entries) == 2
    assert result.gaps is not None
    assert len(result.gaps.records) == 2
    assert result.catalysts is not None
    assert len(result.catalysts.records) == 1
    assert result.scores is not None
    assert len(result.scores.records) == 2
    assert result.briefing is not None
    assert len(result.briefing.records) == 2
    assert result.dashboard is not None
    assert len(result.dashboard.records) == 2
    assert result.dashboard.as_of == AS_OF


def test_i02_deterministic_repeated_execution() -> None:
    request = _request()
    first = run_intelligence_pipeline(request)
    second = run_intelligence_pipeline(request)
    assert first.outcome == second.outcome == PipelineOutcome.COMPLETED_DASHBOARD
    assert first.dashboard is not None and second.dashboard is not None
    assert first.dashboard.dashboard_output_id == second.dashboard.dashboard_output_id
    assert first.dashboard.provenance.config_fingerprint == (
        second.dashboard.provenance.config_fingerprint
    )
    assert first.dashboard.provenance.input_fingerprint == (
        second.dashboard.provenance.input_fingerprint
    )
    assert first.scores is not None and second.scores is not None
    assert first.scores.provenance.input_fingerprint == second.scores.provenance.input_fingerprint
    assert first.bindings == second.bindings
    assert first.provenance.executed_stages == second.provenance.executed_stages


def test_i03_empty_success_path_through_applicable_stages() -> None:
    result = run_intelligence_pipeline(
        _request(
            candidates=(
                WatchlistCandidate(instrument_key="bergama:equity:us:zzzz", local_symbol="ZZZZ"),
            ),
            bars=(),
            events=(),
        )
    )
    assert result.outcome == PipelineOutcome.COMPLETED_DASHBOARD
    assert result.watchlist is not None and result.watchlist.entries == ()
    assert result.gaps is not None and result.gaps.records == ()
    assert result.catalysts is not None and result.catalysts.records == ()
    assert result.scores is not None and result.scores.records == ()
    assert result.briefing is not None and result.briefing.records == ()
    assert result.dashboard is not None and result.dashboard.records == ()
    # Empty Catalyst preserved as object, not None (semantic material for Score).
    assert result.catalysts is not None
    assert result.gaps is not None


def test_i04_fail_closed_required_stage_behavior() -> None:
    # Future known_at relative to as_of → catalyst stage fails closed.
    future_known = AS_OF + timedelta(hours=1)
    result = run_intelligence_pipeline(
        _request(
            events=(
                make_news(
                    headline="Future leak",
                    summary="Should fail PIT",
                    url_ref="https://example.invalid/news/future",
                    topics=("earnings",),
                    occurred_at=AS_OF - timedelta(hours=1),
                    effective_at=AS_OF - timedelta(hours=1),
                    known_at=future_known,
                    ingested_at=future_known + timedelta(seconds=1),
                    source=source(provider="fixture", source_event_id="future-1"),
                    instrument=instrument(
                        instrument_key="bergama:equity:us:aapl", local_symbol="AAPL"
                    ),
                ),
            )
        )
    )
    assert result.outcome == PipelineOutcome.REQUIRED_STAGE_FAILED
    assert result.failed_stage == "catalyst"
    assert result.dashboard is None
    assert result.scores is None


def test_i05_provenance_binding_continuity() -> None:
    result = run_intelligence_pipeline(_request())
    assert result.bindings is not None
    assert result.provenance.as_of == AS_OF
    assert result.provenance.outcome == PipelineOutcome.COMPLETED_DASHBOARD
    assert result.watchlist is not None
    assert (
        result.provenance.watchlist_config_fingerprint
        == result.watchlist.provenance.config_fingerprint
    )
    assert result.gaps is not None
    assert result.provenance.gap_input_fingerprint == result.gaps.provenance.input_fingerprint
    assert result.catalysts is not None
    assert (
        result.provenance.catalyst_config_fingerprint
        == result.catalysts.provenance.config_fingerprint
    )
    assert result.scores is not None
    assert result.provenance.score_config_fingerprint == result.scores.provenance.config_fingerprint
    assert result.briefing is not None
    assert (
        result.provenance.briefing_input_fingerprint == result.briefing.provenance.input_fingerprint
    )
    assert result.dashboard is not None
    assert (
        result.provenance.dashboard_config_fingerprint
        == result.dashboard.provenance.config_fingerprint
    )
    assert result.bindings.dashboard_policy_version_id == result.dashboard.policy_version_id
