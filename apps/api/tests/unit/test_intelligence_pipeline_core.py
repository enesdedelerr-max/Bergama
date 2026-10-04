"""Unit tests for Intelligence Pipeline Core (Issue #126)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from app.dashboard.models import DashboardConfig, DashboardPresentationOutput, DashboardRequest
from app.intelligence_pipeline import (
    GLOBAL_OUTCOME_FAMILIES,
    ISSUE_1_REACHABLE_OUTCOMES,
    MODEL_PARTICIPATION,
    STAGE_ORDER,
    PipelineOutcome,
    PipelineRequest,
    run_intelligence_pipeline,
)
from app.intelligence_pipeline.policy import (
    OUTCOME_ADMISSION_REJECTED,
    OUTCOME_COMPLETED_ADE_ABSTAIN,
    OUTCOME_COMPLETED_ADE_ACCEPT,
    OUTCOME_COMPLETED_DASHBOARD,
    OUTCOME_COMPLETED_HUMAN_REVIEW,
    OUTCOME_REQUIRED_STAGE_FAILED,
)
from app.premarket.catalyst.models import (
    CatalystClassificationRule,
    CatalystCollection,
    CatalystConfig,
    CatalystProvenance,
)
from app.premarket.gap.models import GapCollection, GapConfig, GapProvenance
from app.premarket.morning_briefing.models import (
    BriefingCollection,
    BriefingConfig,
    BriefingProvenance,
    BriefingRequest,
)
from app.premarket.scoring.models import ScoreCollection, ScoreConfig, ScoreProvenance, ScoreRequest
from app.premarket.watchlist.models import (
    Watchlist,
    WatchlistCandidate,
    WatchlistConfig,
    WatchlistGenerationRequest,
    WatchlistInclusionRule,
    WatchlistProvenance,
)
from pydantic import ValidationError
from tests.support.market_data_fixtures import instrument, make_bar, make_news, source

AS_OF = datetime(2026, 7, 17, 14, 0, tzinfo=UTC)
DAY1 = datetime(2026, 7, 15, 20, 0, tzinfo=UTC)
DAY2 = datetime(2026, 7, 16, 20, 0, tzinfo=UTC)
FP_A = "a" * 64
FP_B = "b" * 64


def _watchlist_config(
    *,
    keys: tuple[str, ...] = ("bergama:equity:us:aapl",),
) -> WatchlistConfig:
    return WatchlistConfig(
        rules=(
            WatchlistInclusionRule(
                rule_id="core",
                rule_priority=1,
                inclusion_reason="approved",
                allowed_instrument_keys=keys,
            ),
        )
    )


def _catalyst_config() -> CatalystConfig:
    return CatalystConfig(
        classification_rules=(
            CatalystClassificationRule(
                rule_id="earnings-topic",
                rule_priority=10,
                catalyst_type="earnings",
                match_topics=("earnings",),
            ),
        )
    )


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


def _valid_request(**overrides: Any) -> PipelineRequest:
    payload: dict[str, Any] = {
        "as_of": AS_OF,
        "candidates": (
            WatchlistCandidate(instrument_key="bergama:equity:us:aapl", local_symbol="AAPL"),
        ),
        "watchlist_config": _watchlist_config(),
        "bars": (
            _bar("bergama:equity:us:aapl", "AAPL", DAY1, "100", "100", "a1"),
            _bar("bergama:equity:us:aapl", "AAPL", DAY2, "110", "111", "a2"),
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
        "catalyst_config": _catalyst_config(),
        "score_config": ScoreConfig(),
        "briefing_config": BriefingConfig(),
        "dashboard_config": DashboardConfig(),
    }
    payload.update(overrides)
    return PipelineRequest(**payload)


def _empty_watchlist() -> Watchlist:
    return Watchlist(
        evaluation_timestamp=AS_OF,
        entries=(),
        provenance=WatchlistProvenance(
            config_fingerprint=FP_A,
            input_fingerprint=FP_B,
            ordering_policy_id="rule_priority_asc_instrument_key_asc",
            source_identifiers=(),
        ),
    )


def _empty_gap() -> GapCollection:
    return GapCollection(
        as_of=AS_OF,
        records=(),
        provenance=GapProvenance(
            config_fingerprint=FP_A,
            input_fingerprint=FP_B,
            ordering_policy_id="abs_gap_desc_instrument_key_asc_id_asc",
            selection_policy_id="two_bars_by_close_time_v1",
            source_identifiers=(),
        ),
    )


def _empty_catalyst() -> CatalystCollection:
    return CatalystCollection(
        as_of=AS_OF,
        records=(),
        provenance=CatalystProvenance(
            config_fingerprint=FP_A,
            input_fingerprint=FP_B,
            ordering_policy_id=("known_at_asc_event_time_asc_type_asc_instrument_key_asc_id_asc"),
            source_identifiers=(),
        ),
    )


def _empty_scores() -> ScoreCollection:
    return ScoreCollection(
        as_of=AS_OF,
        records=(),
        provenance=ScoreProvenance(
            config_fingerprint=FP_A,
            input_fingerprint=FP_B,
            ordering_policy_id="score_desc_instrument_key_asc_score_record_id_asc",
            policy_version_id="premarket.scoring.policy.v1",
            weight_profile_id="default_v1",
            source_identifiers=(),
        ),
    )


def _empty_briefing() -> BriefingCollection:
    return BriefingCollection(
        briefing_id=FP_A,
        policy_version_id="morning-briefing.policy.v1",
        ordering_preservation_policy_id="preserve_premarket_scoring_order.v1",
        as_of=AS_OF,
        records=(),
        provenance=BriefingProvenance(
            policy_version_id="morning-briefing.policy.v1",
            ordering_preservation_policy_id="preserve_premarket_scoring_order.v1",
            identity_specification_id="morning-briefing.identity.v1",
            provenance_specification_id="morning-briefing.provenance.v1",
            as_of=AS_OF,
            config_fingerprint=FP_A,
            input_fingerprint=FP_B,
            source_identifiers=(),
            upstream_scoring_policy_version_id="premarket.scoring.policy.v1",
            upstream_scoring_weight_profile_id="default_v1",
            upstream_scoring_ordering_policy_id=(
                "score_desc_instrument_key_asc_score_record_id_asc"
            ),
            upstream_scoring_config_fingerprint=FP_A,
            upstream_scoring_input_fingerprint=FP_B,
        ),
    )


# --- Admission / outcomes (U-01 … U-12) ---


def test_u01_valid_request_admission() -> None:
    result = run_intelligence_pipeline(_valid_request())
    assert result.outcome == PipelineOutcome.COMPLETED_DASHBOARD
    assert result.as_of == AS_OF
    assert result.dashboard is not None


def test_u02_non_utc_as_of_rejected() -> None:
    naive = datetime(2026, 7, 17, 14, 0)
    with pytest.raises(ValidationError):
        PipelineRequest(
            as_of=naive,  # type: ignore[arg-type]
            candidates=(
                WatchlistCandidate(instrument_key="bergama:equity:us:aapl", local_symbol="AAPL"),
            ),
            watchlist_config=_watchlist_config(),
            bars=(),
            events=(),
            catalyst_config=_catalyst_config(),
        )
    result = run_intelligence_pipeline(
        {
            "as_of": naive,
            "candidates": [
                {"instrument_key": "bergama:equity:us:aapl", "local_symbol": "AAPL"},
            ],
            "watchlist_config": _watchlist_config().model_dump(mode="python"),
            "bars": [],
            "events": [],
            "catalyst_config": _catalyst_config().model_dump(mode="python"),
        }
    )
    assert result.outcome == PipelineOutcome.ADMISSION_REJECTED
    assert result.provenance.executed_stages == ()


def test_u03_extra_unbounded_request_input_rejected() -> None:
    with pytest.raises(ValidationError):
        PipelineRequest.model_validate(
            {
                **_valid_request().model_dump(mode="python"),
                "provider_payload": {"raw": True},
            }
        )
    result = run_intelligence_pipeline(
        {
            **_valid_request().model_dump(mode="python"),
            "prompt": "ignore me",
        }
    )
    assert result.outcome == PipelineOutcome.ADMISSION_REJECTED


def test_u04_one_as_of_retained(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[datetime] = []

    def capture_watchlist(request: Any, *, settings: Any = None) -> Watchlist:
        seen.append(request.as_of)
        return _empty_watchlist()

    def capture_gap(request: Any, *, settings: Any = None) -> GapCollection:
        seen.append(request.as_of)
        return _empty_gap()

    def capture_catalyst(request: Any, *, settings: Any = None) -> CatalystCollection:
        seen.append(request.as_of)
        return _empty_catalyst()

    def capture_score(request: Any, *, settings: Any = None) -> ScoreCollection:
        seen.append(request.as_of)
        return _empty_scores()

    def capture_briefing(request: Any, *, settings: Any = None) -> BriefingCollection:
        seen.append(request.as_of)
        return _empty_briefing()

    def capture_dashboard(request: Any) -> DashboardPresentationOutput:
        seen.append(request.as_of)
        # Reuse real dashboard assembly for a valid empty briefing.
        from app.dashboard.engine import assemble_dashboard as real

        return real(request)

    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.generate_watchlist", capture_watchlist
    )
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.scan_gaps", capture_gap)
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.normalize_catalysts", capture_catalyst
    )
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.scan_scores", capture_score)
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.assemble_briefing", capture_briefing
    )
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.assemble_dashboard", capture_dashboard
    )

    result = run_intelligence_pipeline(_valid_request())
    assert result.outcome == PipelineOutcome.COMPLETED_DASHBOARD
    assert result.as_of == AS_OF
    assert seen == [AS_OF] * 6


def test_u05_admission_rejected_semantics() -> None:
    result = run_intelligence_pipeline({"as_of": "not-a-datetime"})
    assert result.outcome.value == OUTCOME_ADMISSION_REJECTED
    assert result.failed_stage is None
    assert result.dashboard is None
    assert result.watchlist is None
    assert result.failure_error_type == "PipelineAdmissionError"


def test_u06_required_stage_failed_semantics(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(request: Any, *, settings: Any = None) -> Watchlist:
        raise RuntimeError("watchlist_boom")

    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.generate_watchlist", boom)
    result = run_intelligence_pipeline(_valid_request())
    assert result.outcome.value == OUTCOME_REQUIRED_STAGE_FAILED
    assert result.failed_stage == "watchlist"
    assert result.failure_error_type == "RuntimeError"
    assert result.failure_detail == "watchlist_boom"
    assert result.dashboard is None


def test_u07_completed_dashboard_semantics() -> None:
    result = run_intelligence_pipeline(_valid_request())
    assert result.outcome.value == OUTCOME_COMPLETED_DASHBOARD
    assert result.failed_stage is None
    assert result.dashboard is not None
    assert result.provenance.outcome == PipelineOutcome.COMPLETED_DASHBOARD


def test_u08_global_six_outcome_identities_exact() -> None:
    assert GLOBAL_OUTCOME_FAMILIES == (
        OUTCOME_ADMISSION_REJECTED,
        OUTCOME_REQUIRED_STAGE_FAILED,
        OUTCOME_COMPLETED_DASHBOARD,
        OUTCOME_COMPLETED_HUMAN_REVIEW,
        OUTCOME_COMPLETED_ADE_ACCEPT,
        OUTCOME_COMPLETED_ADE_ABSTAIN,
    )
    assert tuple(member.value for member in PipelineOutcome) == GLOBAL_OUTCOME_FAMILIES
    assert len(GLOBAL_OUTCOME_FAMILIES) == 6


def test_u09_issue_1_reachable_outcome_subset_exact() -> None:
    assert ISSUE_1_REACHABLE_OUTCOMES == (
        OUTCOME_ADMISSION_REJECTED,
        OUTCOME_REQUIRED_STAGE_FAILED,
        OUTCOME_COMPLETED_DASHBOARD,
    )
    assert len(ISSUE_1_REACHABLE_OUTCOMES) == 3


def test_u10_bounded_failure_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.scan_gaps",
        MagicMock(side_effect=ValueError("gap_fail")),
    )
    result = run_intelligence_pipeline(_valid_request())
    assert result.outcome == PipelineOutcome.REQUIRED_STAGE_FAILED
    assert result.failed_stage == "gap"
    assert result.failure_detail == "gap_fail"
    assert result.failure_error_type == "ValueError"
    assert result.provenance.failed_stage == "gap"


def test_u11_bounded_provenance() -> None:
    result = run_intelligence_pipeline(_valid_request())
    assert result.provenance.as_of == AS_OF
    assert result.provenance.stage_order == STAGE_ORDER
    assert result.provenance.executed_stages == STAGE_ORDER
    assert result.provenance.watchlist_config_fingerprint is not None
    assert result.provenance.gap_config_fingerprint is not None
    assert result.provenance.catalyst_config_fingerprint is not None
    assert result.provenance.score_config_fingerprint is not None
    assert result.provenance.briefing_config_fingerprint is not None
    assert result.provenance.dashboard_config_fingerprint is not None
    assert result.provenance.failed_stage is None


def test_u12_stable_config_binding_representation() -> None:
    result = run_intelligence_pipeline(_valid_request())
    assert result.bindings is not None
    assert result.bindings.policy_version_id == "intelligence-pipeline.policy.v1"
    assert result.bindings.score_policy_version_id == "premarket.scoring.policy.v1"
    assert result.bindings.briefing_policy_version_id == "morning-briefing.policy.v1"
    assert result.bindings.dashboard_policy_version_id == "dashboard.policy.v1"
    again = run_intelligence_pipeline(_valid_request())
    assert again.bindings == result.bindings


# --- Orchestration (O-01 … O-26) ---


def test_o01_to_o07_stages_execute_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
    order: list[str] = []

    def wl(request: Any, *, settings: Any = None) -> Watchlist:
        assert isinstance(request, WatchlistGenerationRequest)
        order.append("watchlist")
        return _empty_watchlist()

    def gap(request: Any, *, settings: Any = None) -> GapCollection:
        order.append("gap")
        return _empty_gap()

    def cat(request: Any, *, settings: Any = None) -> CatalystCollection:
        order.append("catalyst")
        return _empty_catalyst()

    def score(request: Any, *, settings: Any = None) -> ScoreCollection:
        order.append("score")
        return _empty_scores()

    def briefing(request: Any, *, settings: Any = None) -> BriefingCollection:
        order.append("briefing")
        return _empty_briefing()

    def dashboard(request: Any) -> DashboardPresentationOutput:
        order.append("dashboard")
        from app.dashboard.engine import assemble_dashboard as real

        return real(request)

    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.generate_watchlist", wl)
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.scan_gaps", gap)
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.normalize_catalysts", cat)
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.scan_scores", score)
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.assemble_briefing", briefing)
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.assemble_dashboard", dashboard)

    result = run_intelligence_pipeline(_valid_request())
    assert order == list(STAGE_ORDER)
    assert result.outcome == PipelineOutcome.COMPLETED_DASHBOARD


def test_o08_watchlist_failure_stops_downstream(monkeypatch: pytest.MonkeyPatch) -> None:
    downstream = MagicMock()
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.generate_watchlist",
        MagicMock(side_effect=RuntimeError("wl")),
    )
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.scan_gaps", downstream)
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.normalize_catalysts", downstream)
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.scan_scores", downstream)
    result = run_intelligence_pipeline(_valid_request())
    assert result.outcome == PipelineOutcome.REQUIRED_STAGE_FAILED
    assert result.failed_stage == "watchlist"
    assert downstream.call_count == 0


def test_o09_empty_watchlist_success_continues() -> None:
    # Candidates outside allowlist → successful empty watchlist → continues.
    request = _valid_request(
        candidates=(
            WatchlistCandidate(instrument_key="bergama:equity:us:zzzz", local_symbol="ZZZZ"),
        ),
        bars=(),
        events=(),
    )
    result = run_intelligence_pipeline(request)
    assert result.outcome == PipelineOutcome.COMPLETED_DASHBOARD
    assert result.watchlist is not None
    assert result.watchlist.entries == ()
    assert result.gaps is not None
    assert result.gaps.records == ()
    assert result.catalysts is not None
    assert result.catalysts.records == ()


def test_o10_gap_failure_stops_downstream(monkeypatch: pytest.MonkeyPatch) -> None:
    score = MagicMock()
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.scan_gaps",
        MagicMock(side_effect=RuntimeError("gap")),
    )
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.scan_scores", score)
    result = run_intelligence_pipeline(_valid_request())
    assert result.failed_stage == "gap"
    assert score.call_count == 0


def test_o11_o12_o16_empty_gap_and_catalyst_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    empty_gap = _empty_gap()
    empty_cat = _empty_catalyst()
    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.scan_gaps",
        MagicMock(return_value=empty_gap),
    )
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.normalize_catalysts",
        MagicMock(return_value=empty_cat),
    )

    def capture_score(request: Any, *, settings: Any = None) -> ScoreCollection:
        captured["score_request"] = request
        assert request.gaps is empty_gap
        assert request.catalysts is empty_cat
        assert request.gaps is not None
        assert request.catalysts is not None
        assert request.catalysts is not None  # not collapsed to None
        return _empty_scores()

    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.scan_scores", capture_score)
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.assemble_briefing",
        MagicMock(return_value=_empty_briefing()),
    )

    def dash(request: Any) -> DashboardPresentationOutput:
        from app.dashboard.engine import assemble_dashboard as real

        return real(request)

    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.assemble_dashboard", dash)

    result = run_intelligence_pipeline(_valid_request())
    assert result.outcome == PipelineOutcome.COMPLETED_DASHBOARD
    assert result.gaps is empty_gap
    assert result.catalysts is empty_cat
    assert isinstance(captured["score_request"], ScoreRequest)
    assert captured["score_request"].gaps is empty_gap
    assert captured["score_request"].catalysts is empty_cat


def test_o13_catalyst_failure_stops_downstream(monkeypatch: pytest.MonkeyPatch) -> None:
    score = MagicMock()
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.normalize_catalysts",
        MagicMock(side_effect=RuntimeError("cat")),
    )
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.scan_scores", score)
    result = run_intelligence_pipeline(_valid_request())
    assert result.failed_stage == "catalyst"
    assert score.call_count == 0


def test_o14_o15_empty_catalyst_object_passed(monkeypatch: pytest.MonkeyPatch) -> None:
    empty_cat = _empty_catalyst()
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.normalize_catalysts",
        MagicMock(return_value=empty_cat),
    )
    seen: list[Any] = []

    def capture_score(request: Any, *, settings: Any = None) -> ScoreCollection:
        seen.append(request.catalysts)
        return _empty_scores()

    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.scan_scores", capture_score)
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.assemble_briefing",
        MagicMock(return_value=_empty_briefing()),
    )
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.assemble_dashboard",
        lambda request: __import__(
            "app.dashboard.engine", fromlist=["assemble_dashboard"]
        ).assemble_dashboard(request),
    )
    result = run_intelligence_pipeline(_valid_request())
    assert result.outcome == PipelineOutcome.COMPLETED_DASHBOARD
    assert seen[0] is empty_cat
    assert seen[0] is not None


def test_o17_score_failure_stops_briefing_dashboard(monkeypatch: pytest.MonkeyPatch) -> None:
    briefing = MagicMock()
    dashboard = MagicMock()
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.scan_scores",
        MagicMock(side_effect=RuntimeError("score")),
    )
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.assemble_briefing", briefing)
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.assemble_dashboard", dashboard)
    result = run_intelligence_pipeline(_valid_request())
    assert result.failed_stage == "score"
    assert briefing.call_count == 0
    assert dashboard.call_count == 0


def test_o18_empty_score_success_continues(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.scan_scores",
        MagicMock(return_value=_empty_scores()),
    )
    result = run_intelligence_pipeline(_valid_request())
    assert result.outcome == PipelineOutcome.COMPLETED_DASHBOARD
    assert result.scores is not None
    assert result.scores.records == ()
    assert result.briefing is not None
    assert result.dashboard is not None


def test_o19_briefing_failure_stops_dashboard(monkeypatch: pytest.MonkeyPatch) -> None:
    dashboard = MagicMock()
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.assemble_briefing",
        MagicMock(side_effect=RuntimeError("brief")),
    )
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.assemble_dashboard", dashboard)
    result = run_intelligence_pipeline(_valid_request())
    assert result.failed_stage == "briefing"
    assert dashboard.call_count == 0


def test_o20_empty_briefing_success_continues(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.assemble_briefing",
        MagicMock(return_value=_empty_briefing()),
    )
    result = run_intelligence_pipeline(_valid_request())
    assert result.outcome == PipelineOutcome.COMPLETED_DASHBOARD
    assert result.briefing is not None
    assert result.briefing.records == ()
    assert result.dashboard is not None


def test_o21_dashboard_failure_required_stage_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.assemble_dashboard",
        MagicMock(side_effect=RuntimeError("dash")),
    )
    result = run_intelligence_pipeline(_valid_request())
    assert result.outcome == PipelineOutcome.REQUIRED_STAGE_FAILED
    assert result.failed_stage == "dashboard"


def test_o22_dashboard_success_completed_dashboard() -> None:
    result = run_intelligence_pipeline(_valid_request())
    assert result.outcome == PipelineOutcome.COMPLETED_DASHBOARD
    assert result.dashboard is not None


def test_o23_same_as_of_propagated() -> None:
    result = run_intelligence_pipeline(_valid_request())
    assert result.as_of == AS_OF
    assert result.watchlist is not None
    assert result.watchlist.evaluation_timestamp == AS_OF
    assert result.gaps is not None
    assert result.gaps.as_of == AS_OF
    assert result.catalysts is not None
    assert result.catalysts.as_of == AS_OF
    assert result.scores is not None
    assert result.scores.as_of == AS_OF
    assert result.briefing is not None
    assert result.briefing.as_of == AS_OF
    assert result.dashboard is not None
    assert result.dashboard.as_of == AS_OF


def test_o24_o25_o26_public_entrypoints_typed_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, type[Any]] = {}

    def wl(request: Any, *, settings: Any = None) -> Watchlist:
        calls["watchlist"] = type(request)
        assert not hasattr(request, "_from_parts")
        return _empty_watchlist()

    def gap(request: Any, *, settings: Any = None) -> GapCollection:
        calls["gap"] = type(request)
        return _empty_gap()

    def cat(request: Any, *, settings: Any = None) -> CatalystCollection:
        calls["catalyst"] = type(request)
        return _empty_catalyst()

    def score(request: Any, *, settings: Any = None) -> ScoreCollection:
        calls["score"] = type(request)
        return _empty_scores()

    def briefing(request: Any, *, settings: Any = None) -> BriefingCollection:
        calls["briefing"] = type(request)
        assert isinstance(request, BriefingRequest)
        return _empty_briefing()

    def dashboard(request: Any) -> DashboardPresentationOutput:
        calls["dashboard"] = type(request)
        assert isinstance(request, DashboardRequest)
        from app.dashboard.engine import assemble_dashboard as real

        return real(request)

    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.generate_watchlist", wl)
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.scan_gaps", gap)
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.normalize_catalysts", cat)
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.scan_scores", score)
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.assemble_briefing", briefing)
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.assemble_dashboard", dashboard)

    # Ensure orchestrator module does not call *_from_parts helpers.
    import app.intelligence_pipeline.orchestrator as orch

    source = Path(orch.__file__).read_text(encoding="utf-8")
    assert "generate_watchlist_from_parts" not in source
    assert "scan_gaps_from_parts" not in source
    assert "normalize_catalysts_from_parts" not in source
    assert "scan_scores_from_parts" not in source
    assert "assemble_briefing_from_parts" not in source
    assert "assemble_dashboard_from_parts" not in source

    result = run_intelligence_pipeline(_valid_request())
    assert result.outcome == PipelineOutcome.COMPLETED_DASHBOARD
    assert calls["watchlist"] is WatchlistGenerationRequest
    assert calls["score"] is ScoreRequest
    assert calls["briefing"] is BriefingRequest
    assert calls["dashboard"] is DashboardRequest


def test_model_participation_unauthorized() -> None:
    assert MODEL_PARTICIPATION == "UNAUTHORIZED"
