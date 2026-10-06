"""Integration boundary tests for Intelligence Pipeline Core (Issue #126/#128)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock

import pytest
from app.ai_decision_engine.models import AdeConfig, AdeOutcomeKind, AdeProvenance, AdeResult
from app.ai_decision_engine.policy import (
    ACCEPTANCE_SPECIFICATION_V1,
    DERIVATION_ATTRIBUTION_V1,
    DIGEST_METHOD_V1,
    IDENTITY_SPECIFICATION_V1,
    PROVENANCE_SPECIFICATION_V1,
)
from app.ai_decision_engine.policy import (
    POLICY_VERSION_V1 as ADE_POLICY_VERSION_V1,
)
from app.ai_decision_engine.reasons import AdeReasonFamily
from app.dashboard.models import DashboardConfig
from app.human_review.models import HumanReviewConfig, HumanReviewRecordedAttestation
from app.human_review.policy import POLICY_VERSION_V1 as HR_POLICY_VERSION_V1
from app.intelligence_pipeline import (
    GLOBAL_OUTCOME_FAMILIES,
    STAGE_ORDER,
    PipelineOutcome,
    PipelineRequest,
    replay_intelligence_pipeline,
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


VALID_ATTESTATION = HumanReviewRecordedAttestation(
    recorded_payload="integration-human-recorded-attestation-v1"
)


def test_i128_01_hr_off_ade_off_completed_dashboard() -> None:
    result = run_intelligence_pipeline(_request())
    assert result.outcome == PipelineOutcome.COMPLETED_DASHBOARD
    assert result.human_review is None
    assert result.ade is None


def test_i128_02_hr_on_valid_attestation_ade_off_completed_human_review() -> None:
    result = run_intelligence_pipeline(
        _request(hr_requested=True, hr_attestation=VALID_ATTESTATION)
    )
    assert result.outcome == PipelineOutcome.COMPLETED_HUMAN_REVIEW
    assert result.human_review is not None
    assert result.ade is None
    assert result.dashboard is not None
    assert result.human_review.dashboard_output_id == result.dashboard.dashboard_output_id
    assert result.bindings is not None
    assert result.bindings.human_review_policy_version_id == HR_POLICY_VERSION_V1
    assert result.provenance.human_review_output_id == result.human_review.human_review_output_id
    assert result.provenance.recorded_attestation_fingerprint is not None


def test_i128_03_hr_on_missing_attestation_admission_rejected() -> None:
    result = run_intelligence_pipeline(_request(hr_requested=True, hr_attestation=None))
    assert result.outcome == PipelineOutcome.ADMISSION_REJECTED
    assert result.failure_detail == "human_review_attestation_required"


def test_i128_04_hr_on_invalid_attestation_stage_failed_no_ade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ade = MagicMock()
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.evaluate_ade", ade)
    first = run_intelligence_pipeline(_request())
    assert first.dashboard is not None
    bad = HumanReviewRecordedAttestation(recorded_payload=first.dashboard.dashboard_output_id)
    result = run_intelligence_pipeline(
        _request(hr_requested=True, hr_attestation=bad, ade_requested=True)
    )
    assert result.outcome == PipelineOutcome.REQUIRED_STAGE_FAILED
    assert result.failed_stage == "human_review"
    assert result.ade is None
    assert ade.call_count == 0


def test_i128_05_ade_without_hr_admission_rejected_no_ade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ade = MagicMock()
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.evaluate_ade", ade)
    result = run_intelligence_pipeline(_request(ade_requested=True, hr_requested=False))
    assert result.outcome == PipelineOutcome.ADMISSION_REJECTED
    assert result.failure_detail == "ade_requires_human_review"
    assert ade.call_count == 0


def test_i128_06_valid_hr_ade_accept() -> None:
    result = run_intelligence_pipeline(
        _request(
            hr_requested=True,
            ade_requested=True,
            hr_attestation=VALID_ATTESTATION,
        )
    )
    assert result.outcome == PipelineOutcome.COMPLETED_ADE_ACCEPT
    assert result.human_review is not None
    assert result.ade is not None
    assert result.ade.outcome_kind is AdeOutcomeKind.AUTHORITATIVE_DECISION
    assert result.ade.human_review_output_id == result.human_review.human_review_output_id
    assert result.bindings is not None
    assert result.bindings.ade_policy_version_id == ADE_POLICY_VERSION_V1
    assert result.provenance.ade_decision_id == result.ade.decision_id
    assert result.provenance.ade_evidence_fingerprint is not None


def test_i128_07_valid_hr_ade_abstain(monkeypatch: pytest.MonkeyPatch) -> None:
    def abstain(request: object) -> AdeResult:
        from app.ai_decision_engine.models import AdeEvaluationRequest

        assert isinstance(request, AdeEvaluationRequest)
        assert request.human_review is not None
        return AdeResult(
            outcome_kind=AdeOutcomeKind.EXPLICIT_ABSTENTION,
            policy_version_id=ADE_POLICY_VERSION_V1,
            as_of=request.as_of,
            reason_family=AdeReasonFamily.DETERMINISTIC_ACCEPTANCE_NOT_ESTABLISHED,
            decision_id=None,
            human_review_output_id=request.human_review.human_review_output_id,
            provenance=AdeProvenance(
                policy_version_id=ADE_POLICY_VERSION_V1,
                identity_specification_id=IDENTITY_SPECIFICATION_V1,
                provenance_specification_id=PROVENANCE_SPECIFICATION_V1,
                acceptance_specification_id=ACCEPTANCE_SPECIFICATION_V1,
                digest_method_id=DIGEST_METHOD_V1,
                derivation_attribution_id=DERIVATION_ATTRIBUTION_V1,
                as_of=request.as_of,
                human_review_output_id=request.human_review.human_review_output_id,
                human_review_policy_version_id=request.human_review.policy_version_id,
                human_review_identity_specification_id=(
                    request.human_review.identity_specification_id
                ),
                human_review_provenance_specification_id=(
                    request.human_review.provenance_specification_id
                ),
                human_review_config_fingerprint=(
                    request.human_review.provenance.config_fingerprint
                ),
                human_review_input_fingerprint=request.human_review.provenance.input_fingerprint,
                recorded_attestation_fingerprint=(
                    request.human_review.provenance.recorded_attestation_fingerprint
                ),
                recorded_attestation_payload=request.human_review.attestation.recorded_payload,
                config_fingerprint="c" * 64,
                evidence_fingerprint="e" * 64,
            ),
            detail="explicit_abstention_fixture",
        )

    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.evaluate_ade", abstain)
    result = run_intelligence_pipeline(
        _request(
            hr_requested=True,
            ade_requested=True,
            hr_attestation=VALID_ATTESTATION,
        )
    )
    assert result.outcome == PipelineOutcome.COMPLETED_ADE_ABSTAIN
    assert result.human_review is not None
    assert result.ade is not None
    assert result.ade.outcome_kind is AdeOutcomeKind.EXPLICIT_ABSTENTION


def test_i128_08_hr_exception_no_ade(monkeypatch: pytest.MonkeyPatch) -> None:
    ade = MagicMock()
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.assemble_human_review",
        MagicMock(side_effect=RuntimeError("hr_fail")),
    )
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.evaluate_ade", ade)
    result = run_intelligence_pipeline(
        _request(
            hr_requested=True,
            ade_requested=True,
            hr_attestation=VALID_ATTESTATION,
        )
    )
    assert result.outcome == PipelineOutcome.REQUIRED_STAGE_FAILED
    assert result.failed_stage == "human_review"
    assert ade.call_count == 0


def test_i128_09_ade_exception_required_stage_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.evaluate_ade",
        MagicMock(side_effect=RuntimeError("ade_fail")),
    )
    result = run_intelligence_pipeline(
        _request(
            hr_requested=True,
            ade_requested=True,
            hr_attestation=VALID_ATTESTATION,
        )
    )
    assert result.outcome == PipelineOutcome.REQUIRED_STAGE_FAILED
    assert result.failed_stage == "ade"
    assert result.human_review is not None


def test_i128_10_dashboard_public_output_passed_to_hr(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}
    real = __import__(
        "app.human_review.engine", fromlist=["assemble_human_review"]
    ).assemble_human_review

    def capture(request: object) -> object:
        captured["dashboard"] = request.dashboard
        return real(request)

    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.assemble_human_review", capture)
    result = run_intelligence_pipeline(
        _request(hr_requested=True, hr_attestation=VALID_ATTESTATION)
    )
    assert result.outcome == PipelineOutcome.COMPLETED_HUMAN_REVIEW
    assert result.dashboard is not None
    assert captured["dashboard"] is result.dashboard


def test_i128_11_successful_hr_output_passed_to_ade(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}
    real = __import__("app.ai_decision_engine.engine", fromlist=["evaluate_ade"]).evaluate_ade

    def capture(request: object) -> object:
        captured["human_review"] = request.human_review
        return real(request)

    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.evaluate_ade", capture)
    result = run_intelligence_pipeline(
        _request(
            hr_requested=True,
            ade_requested=True,
            hr_attestation=VALID_ATTESTATION,
        )
    )
    assert result.outcome == PipelineOutcome.COMPLETED_ADE_ACCEPT
    assert result.human_review is not None
    assert captured["human_review"] is result.human_review


def test_i128_12_same_as_of_observed_by_hr_and_ade(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[datetime] = []
    real_hr = __import__(
        "app.human_review.engine", fromlist=["assemble_human_review"]
    ).assemble_human_review
    real_ade = __import__("app.ai_decision_engine.engine", fromlist=["evaluate_ade"]).evaluate_ade

    def capture_hr(request: object) -> object:
        seen.append(request.as_of)
        return real_hr(request)

    def capture_ade(request: object) -> object:
        seen.append(request.as_of)
        return real_ade(request)

    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.assemble_human_review", capture_hr)
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.evaluate_ade", capture_ade)
    result = run_intelligence_pipeline(
        _request(
            hr_requested=True,
            ade_requested=True,
            hr_attestation=VALID_ATTESTATION,
        )
    )
    assert result.outcome == PipelineOutcome.COMPLETED_ADE_ACCEPT
    assert seen == [AS_OF, AS_OF]
    assert result.human_review is not None
    assert result.human_review.as_of == AS_OF
    assert result.ade is not None
    assert result.ade.as_of == AS_OF


def test_i128_13_hr_config_policy_binding_stable() -> None:
    config = HumanReviewConfig()
    first = run_intelligence_pipeline(
        _request(hr_requested=True, hr_attestation=VALID_ATTESTATION, hr_config=config)
    )
    second = run_intelligence_pipeline(
        _request(hr_requested=True, hr_attestation=VALID_ATTESTATION, hr_config=config)
    )
    assert first.bindings == second.bindings
    assert first.bindings is not None
    assert first.bindings.human_review_policy_version_id == HR_POLICY_VERSION_V1


def test_i128_14_ade_config_policy_binding_stable() -> None:
    config = AdeConfig()
    first = run_intelligence_pipeline(
        _request(
            hr_requested=True,
            ade_requested=True,
            hr_attestation=VALID_ATTESTATION,
            ade_config=config,
        )
    )
    second = run_intelligence_pipeline(
        _request(
            hr_requested=True,
            ade_requested=True,
            hr_attestation=VALID_ATTESTATION,
            ade_config=config,
        )
    )
    assert first.bindings == second.bindings
    assert first.bindings is not None
    assert first.bindings.ade_policy_version_id == ADE_POLICY_VERSION_V1


def test_i128_15_no_synthetic_human_approval() -> None:
    result = run_intelligence_pipeline(
        _request(hr_requested=True, hr_attestation=VALID_ATTESTATION)
    )
    assert result.human_review is not None
    assert result.human_review.attestation.recorded_payload == VALID_ATTESTATION.recorded_payload
    assert not hasattr(result.human_review, "approved")


def test_i128_16_no_automatic_hr_when_not_requested(monkeypatch: pytest.MonkeyPatch) -> None:
    hr = MagicMock()
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.assemble_human_review", hr)
    result = run_intelligence_pipeline(_request())
    assert result.outcome == PipelineOutcome.COMPLETED_DASHBOARD
    assert hr.call_count == 0


def test_i128_17_no_ade_after_unsuccessful_hr(monkeypatch: pytest.MonkeyPatch) -> None:
    ade = MagicMock()
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.assemble_human_review",
        MagicMock(side_effect=RuntimeError("hr")),
    )
    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.evaluate_ade", ade)
    result = run_intelligence_pipeline(
        _request(
            hr_requested=True,
            ade_requested=True,
            hr_attestation=VALID_ATTESTATION,
        )
    )
    assert result.failed_stage == "human_review"
    assert ade.call_count == 0


def test_i128_18_all_six_global_outcomes_reachable(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: set[str] = set()

    rejected = run_intelligence_pipeline({"as_of": "bad"})
    seen.add(rejected.outcome.value)

    future_known = AS_OF + timedelta(hours=1)
    failed = run_intelligence_pipeline(
        _request(
            events=(
                make_news(
                    headline="Future leak",
                    summary="Should fail PIT",
                    url_ref="https://example.invalid/news/future-i128",
                    topics=("earnings",),
                    occurred_at=AS_OF - timedelta(hours=1),
                    effective_at=AS_OF - timedelta(hours=1),
                    known_at=future_known,
                    ingested_at=future_known + timedelta(seconds=1),
                    source=source(provider="fixture", source_event_id="future-i128"),
                    instrument=instrument(
                        instrument_key="bergama:equity:us:aapl", local_symbol="AAPL"
                    ),
                ),
            )
        )
    )
    seen.add(failed.outcome.value)

    dashboard = run_intelligence_pipeline(_request())
    seen.add(dashboard.outcome.value)

    hr_only = run_intelligence_pipeline(
        _request(hr_requested=True, hr_attestation=VALID_ATTESTATION)
    )
    seen.add(hr_only.outcome.value)

    accept = run_intelligence_pipeline(
        _request(
            hr_requested=True,
            ade_requested=True,
            hr_attestation=VALID_ATTESTATION,
        )
    )
    seen.add(accept.outcome.value)

    def abstain(request: object) -> AdeResult:
        from app.ai_decision_engine.models import AdeEvaluationRequest

        assert isinstance(request, AdeEvaluationRequest)
        assert request.human_review is not None
        return AdeResult(
            outcome_kind=AdeOutcomeKind.EXPLICIT_ABSTENTION,
            policy_version_id=ADE_POLICY_VERSION_V1,
            as_of=request.as_of,
            reason_family=AdeReasonFamily.DETERMINISTIC_ACCEPTANCE_NOT_ESTABLISHED,
            decision_id=None,
            human_review_output_id=request.human_review.human_review_output_id,
            provenance=AdeProvenance(
                policy_version_id=ADE_POLICY_VERSION_V1,
                identity_specification_id=IDENTITY_SPECIFICATION_V1,
                provenance_specification_id=PROVENANCE_SPECIFICATION_V1,
                acceptance_specification_id=ACCEPTANCE_SPECIFICATION_V1,
                digest_method_id=DIGEST_METHOD_V1,
                derivation_attribution_id=DERIVATION_ATTRIBUTION_V1,
                as_of=request.as_of,
                human_review_output_id=request.human_review.human_review_output_id,
                config_fingerprint="c" * 64,
                evidence_fingerprint="f" * 64,
            ),
            detail="explicit_abstention_fixture",
        )

    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.evaluate_ade", abstain)
    abstain_result = run_intelligence_pipeline(
        _request(
            hr_requested=True,
            ade_requested=True,
            hr_attestation=VALID_ATTESTATION,
        )
    )
    seen.add(abstain_result.outcome.value)

    assert seen == set(GLOBAL_OUTCOME_FAMILIES)
    assert len(seen) == 6


def test_i128_19_issue_1_stage_order_unchanged() -> None:
    result = run_intelligence_pipeline(_request())
    assert result.provenance.stage_order == STAGE_ORDER
    assert result.provenance.executed_stages == STAGE_ORDER


def test_i128_20_empty_gap_semantics_unchanged() -> None:
    result = run_intelligence_pipeline(
        _request(
            candidates=(
                WatchlistCandidate(instrument_key="bergama:equity:us:zzzz", local_symbol="ZZZZ"),
            ),
            bars=(),
            events=(),
            hr_requested=True,
            hr_attestation=VALID_ATTESTATION,
        )
    )
    assert result.outcome == PipelineOutcome.COMPLETED_HUMAN_REVIEW
    assert result.gaps is not None
    assert result.gaps.records == ()


def test_i128_21_empty_catalyst_semantics_unchanged() -> None:
    result = run_intelligence_pipeline(
        _request(events=(), hr_requested=True, hr_attestation=VALID_ATTESTATION)
    )
    assert result.outcome == PipelineOutcome.COMPLETED_HUMAN_REVIEW
    assert result.catalysts is not None
    assert result.catalysts.records == ()


def test_i130_01_public_boundary_replay() -> None:
    """I-R1: replay through public run_intelligence_pipeline boundary."""
    request = _request()
    expected = run_intelligence_pipeline(request)
    assert expected.provenance.pipeline_fingerprint is not None
    actual = replay_intelligence_pipeline(request, expected=expected)
    assert actual.outcome == expected.outcome
    assert actual.provenance.pipeline_fingerprint == expected.provenance.pipeline_fingerprint
    assert actual.as_of == AS_OF
    assert actual.bindings == expected.bindings
