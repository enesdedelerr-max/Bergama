"""Unit tests for Intelligence Pipeline replay / determinism (Issue #130)."""

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
from app.core.premarket_settings import PremarketSettings
from app.dashboard.models import DashboardConfig
from app.human_review.models import HumanReviewRecordedAttestation
from app.intelligence_pipeline import (
    GLOBAL_OUTCOME_FAMILIES,
    PipelineOutcome,
    PipelineReplayInequalityError,
    PipelineRequest,
    assert_replay_equal,
    replay_intelligence_pipeline,
    run_intelligence_pipeline,
)
from app.intelligence_pipeline.admit import admit_pipeline_request, pin_bindings
from app.intelligence_pipeline.errors import PipelineStageExecutionError
from app.intelligence_pipeline.orchestrator import _normalize_stage_failure
from app.intelligence_pipeline.policy import (
    FAILURE_DETAIL_MAX_LENGTH,
    FINGERPRINT_SCHEMA_ID,
    OUTCOME_COMPLETED_ADE_ABSTAIN,
    OUTCOME_COMPLETED_ADE_ACCEPT,
    OUTCOME_COMPLETED_DASHBOARD,
    OUTCOME_COMPLETED_HUMAN_REVIEW,
    OUTCOME_REQUIRED_STAGE_FAILED,
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
VALID_ATTESTATION = HumanReviewRecordedAttestation(
    recorded_payload="human-recorded-attestation-payload-v1"
)


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


def test_r01_same_request_same_fingerprint() -> None:
    first = run_intelligence_pipeline(_valid_request())
    second = run_intelligence_pipeline(_valid_request())
    assert first.provenance.pipeline_fingerprint is not None
    assert first.provenance.pipeline_fingerprint == second.provenance.pipeline_fingerprint
    assert len(first.provenance.pipeline_fingerprint) == 64
    assert FINGERPRINT_SCHEMA_ID == "intelligence-pipeline.fingerprint.v1"


def test_r02_replay_preserves_as_of_no_wall_clock() -> None:
    from pathlib import Path

    package = Path(__file__).resolve().parents[2] / "app" / "intelligence_pipeline"
    for name in ("orchestrator.py", "replay.py", "admit.py"):
        text = (package / name).read_text(encoding="utf-8")
        assert "datetime.now" not in text
        assert "utcnow" not in text
    request = _valid_request()
    expected = run_intelligence_pipeline(request)
    actual = replay_intelligence_pipeline(request, expected=expected)
    assert actual.as_of == request.as_of == AS_OF
    assert actual.provenance.as_of == AS_OF


def test_r03_settings_mutation_after_admission_isolated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.premarket.watchlist.engine import generate_watchlist as real_generate

    settings = PremarketSettings(enabled=True)
    request = _valid_request(settings=settings)
    admitted = admit_pipeline_request(request)
    assert admitted.settings is not None
    assert admitted.settings is not settings

    seen_enabled: list[bool | None] = []

    def capture_and_mutate(stage_request: Any, *, settings: Any = None) -> Any:
        seen_enabled.append(None if settings is None else bool(settings.enabled))
        # Caller mutates the original PremarketSettings object mid-run.
        request.settings.enabled = False  # type: ignore[union-attr]
        return real_generate(stage_request, settings=settings)

    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.generate_watchlist",
        capture_and_mutate,
    )
    result = run_intelligence_pipeline(request)
    assert result.outcome == PipelineOutcome.COMPLETED_DASHBOARD
    assert seen_enabled == [True]
    assert request.settings is not None
    assert request.settings.enabled is False
    # Fresh admission still snapshots independently from a new caller object.
    fresh = PremarketSettings(enabled=True)
    re_admitted = admit_pipeline_request(_valid_request(settings=fresh))
    fresh.enabled = False
    assert re_admitted.settings is not None
    assert re_admitted.settings.enabled is True
    assert re_admitted.settings is not fresh


def test_r04_dashboard_terminal_replay() -> None:
    request = _valid_request()
    expected = run_intelligence_pipeline(request)
    assert expected.outcome.value == OUTCOME_COMPLETED_DASHBOARD
    actual = replay_intelligence_pipeline(request, expected=expected)
    assert actual.outcome == expected.outcome
    assert actual.provenance.pipeline_fingerprint == expected.provenance.pipeline_fingerprint


def test_r05_human_review_terminal_replay() -> None:
    request = _valid_request(hr_requested=True, hr_attestation=VALID_ATTESTATION)
    expected = run_intelligence_pipeline(request)
    assert expected.outcome.value == OUTCOME_COMPLETED_HUMAN_REVIEW
    actual = replay_intelligence_pipeline(request, expected=expected)
    assert actual.human_review is not None
    assert actual.ade is None


def test_r06_ade_accept_replay() -> None:
    request = _valid_request(
        hr_requested=True,
        ade_requested=True,
        hr_attestation=VALID_ATTESTATION,
        ade_config=AdeConfig(),
    )
    expected = run_intelligence_pipeline(request)
    assert expected.outcome.value == OUTCOME_COMPLETED_ADE_ACCEPT
    actual = replay_intelligence_pipeline(request, expected=expected)
    assert actual.ade is not None
    assert actual.ade.outcome_kind is AdeOutcomeKind.AUTHORITATIVE_DECISION


def test_r07_ade_abstain_replay(monkeypatch: pytest.MonkeyPatch) -> None:
    def abstain(request: object) -> AdeResult:
        from app.ai_decision_engine.models import AdeEvaluationRequest

        assert isinstance(request, AdeEvaluationRequest)
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
                evidence_fingerprint="d" * 64,
            ),
            detail="explicit_abstention_fixture",
        )

    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.evaluate_ade", abstain)
    request = _valid_request(
        hr_requested=True,
        ade_requested=True,
        hr_attestation=VALID_ATTESTATION,
    )
    expected = run_intelligence_pipeline(request)
    assert expected.outcome.value == OUTCOME_COMPLETED_ADE_ABSTAIN
    actual = replay_intelligence_pipeline(request, expected=expected)
    assert actual.outcome == expected.outcome


def test_r08_required_stage_failed_replay(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.intelligence_pipeline.orchestrator.generate_watchlist",
        MagicMock(side_effect=RuntimeError("boom")),
    )
    request = _valid_request()
    expected = run_intelligence_pipeline(request)
    assert expected.outcome.value == OUTCOME_REQUIRED_STAGE_FAILED
    assert expected.provenance.pipeline_fingerprint is not None
    actual = replay_intelligence_pipeline(request, expected=expected)
    assert actual.failed_stage == "watchlist"
    assert actual.failure_error_type == "RuntimeError"


def test_r09_empty_gap_catalyst_preserved_under_replay() -> None:
    request = _valid_request(
        candidates=(
            WatchlistCandidate(instrument_key="bergama:equity:us:zzzz", local_symbol="ZZZZ"),
        ),
        bars=(),
        events=(),
    )
    expected = run_intelligence_pipeline(request)
    assert expected.gaps is not None and expected.gaps.records == ()
    assert expected.catalysts is not None and expected.catalysts.records == ()
    actual = replay_intelligence_pipeline(request, expected=expected)
    assert actual.gaps is not None and actual.gaps.records == ()
    assert actual.catalysts is not None and actual.catalysts.records == ()


def test_r10_replay_mismatch_raises() -> None:
    expected = run_intelligence_pipeline(_valid_request())
    other = run_intelligence_pipeline(
        _valid_request(
            candidates=(
                WatchlistCandidate(instrument_key="bergama:equity:us:msft", local_symbol="MSFT"),
            ),
            watchlist_config=_watchlist_config(keys=("bergama:equity:us:msft",)),
            bars=(
                _bar("bergama:equity:us:msft", "MSFT", DAY1, "50", "50", "m1"),
                _bar("bergama:equity:us:msft", "MSFT", DAY2, "55", "56", "m2"),
            ),
            events=(),
        )
    )
    with pytest.raises(PipelineReplayInequalityError) as exc_info:
        assert_replay_equal(expected, other)
    assert exc_info.value.mismatches
    assert len(GLOBAL_OUTCOME_FAMILIES) == 6


def test_r11_no_hr_synthesis_no_ade_without_hr() -> None:
    rejected = run_intelligence_pipeline(_valid_request(hr_requested=False, ade_requested=True))
    assert rejected.outcome == PipelineOutcome.ADMISSION_REJECTED
    assert rejected.failure_detail == "ade_requires_human_review"
    replayed = replay_intelligence_pipeline(
        _valid_request(hr_requested=False, ade_requested=True),
        expected=rejected,
    )
    assert replayed.outcome == PipelineOutcome.ADMISSION_REJECTED
    assert replayed.human_review is None
    assert replayed.ade is None
    assert replayed.provenance.pipeline_fingerprint is None


def test_r12_failure_detail_bounded() -> None:
    class Exploding(Exception):
        def __init__(self) -> None:
            self.detail = "x" * (FAILURE_DETAIL_MAX_LENGTH + 50)

    normalized = _normalize_stage_failure("watchlist", Exploding())
    assert isinstance(normalized, PipelineStageExecutionError)
    assert normalized.detail is not None
    assert len(normalized.detail) == FAILURE_DETAIL_MAX_LENGTH


def test_r13_pipeline_stage_execution_error_normalization() -> None:
    class DomainErr(Exception):
        def __init__(self) -> None:
            self.detail = "stage_domain_code"

    normalized = _normalize_stage_failure("gap", DomainErr())
    assert isinstance(normalized, PipelineStageExecutionError)
    assert normalized.stage == "gap"
    assert normalized.detail == "stage_domain_code"
    assert normalized.upstream_error_type == "DomainErr"


def test_r14_six_outcomes_unchanged() -> None:
    assert GLOBAL_OUTCOME_FAMILIES == (
        "admission_rejected",
        "required_stage_failed",
        "completed_dashboard",
        "completed_human_review",
        "completed_ade_accept",
        "completed_ade_abstain",
    )
    assert tuple(member.value for member in PipelineOutcome) == GLOBAL_OUTCOME_FAMILIES


def test_r_bindings_stable_across_replay() -> None:
    request = _valid_request()
    expected = run_intelligence_pipeline(request)
    actual = replay_intelligence_pipeline(request, expected=expected)
    assert expected.bindings == actual.bindings
    assert expected.bindings == pin_bindings(admit_pipeline_request(request))
