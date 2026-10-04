"""Unit tests for AI Decision Engine Foundation (Policy Version v1)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from app.ai_decision_engine import (
    FROZEN_REASON_FAMILIES,
    MODEL_PARTICIPATION,
    POLICY_VERSION_V1,
    AdeConfig,
    AdeEvaluationRequest,
    AdeModelParticipationError,
    AdeOutcomeKind,
    AdeReasonFamily,
    AdeReplayInequalityError,
    AdeResult,
    AdeUnauthorizedInputError,
    assert_replay_equal,
    evaluate_ade,
    evaluate_ade_from_parts,
    reevaluate,
)
from app.ai_decision_engine.identity import build_ade_decision_id
from app.dashboard.engine import assemble_dashboard_from_parts
from app.human_review import (
    HumanReviewOutput,
    assemble_human_review_from_parts,
)
from app.premarket.morning_briefing import assemble_briefing_from_parts
from app.premarket.scoring.engine import scan_scores
from app.premarket.scoring.models import ScoreConfig, ScoreRequest
from app.premarket.watchlist.models import Watchlist, WatchlistEntry, WatchlistProvenance
from pydantic import ValidationError

AS_OF = datetime(2026, 7, 17, 14, 0, 0, tzinfo=UTC)
AS_OF_OTHER = datetime(2026, 7, 18, 14, 0, 0, tzinfo=UTC)
ATTESTATION = "recorded-human-authority-v1"
HEX_A = "a" * 64
HEX_B = "b" * 64


def _watchlist() -> Watchlist:
    return Watchlist(
        evaluation_timestamp=AS_OF,
        entries=(
            WatchlistEntry(
                instrument_key="bergama:equity:us:aapl",
                local_symbol="AAPL",
                evaluation_timestamp=AS_OF,
                rank=1,
                inclusion_reason="core",
                rule_id="allowlist",
            ),
        ),
        provenance=WatchlistProvenance(
            config_fingerprint=HEX_A,
            input_fingerprint=HEX_B,
            ordering_policy_id="rule_priority_asc_instrument_key_asc",
            source_identifiers=("bergama:equity:us:aapl",),
        ),
    )


def _human_review(*, as_of: datetime = AS_OF, attestation: str = ATTESTATION) -> HumanReviewOutput:
    scores = scan_scores(ScoreRequest(watchlist=_watchlist(), as_of=as_of, config=ScoreConfig()))
    briefing = assemble_briefing_from_parts(scores=scores, as_of=as_of)
    dashboard = assemble_dashboard_from_parts(briefing=briefing, as_of=as_of)
    return assemble_human_review_from_parts(
        dashboard=dashboard, as_of=as_of, attestation=attestation
    )


def test_authoritative_outcome_from_admissible_human_review() -> None:
    review = _human_review()
    result = evaluate_ade_from_parts(human_review=review, as_of=AS_OF)
    assert result.outcome_kind is AdeOutcomeKind.AUTHORITATIVE_DECISION
    assert result.reason_family is AdeReasonFamily.ACCEPTED_GOVERNED_EVIDENCE
    assert result.policy_version_id == POLICY_VERSION_V1
    assert result.decision_id is not None
    assert result.human_review_output_id == review.human_review_output_id
    assert result.provenance.recorded_attestation_payload == ATTESTATION
    assert result.provenance.human_review_output_id == review.human_review_output_id
    assert result.provenance.policy_version_id == POLICY_VERSION_V1


def test_missing_human_review_explicit_abstention() -> None:
    result = evaluate_ade_from_parts(human_review=None, as_of=AS_OF)
    assert result.outcome_kind is AdeOutcomeKind.EXPLICIT_ABSTENTION
    assert result.reason_family is AdeReasonFamily.MISSING_AUTHORIZED_EVIDENCE
    assert result.decision_id is None


def test_cross_as_of_mismatch_fail_closed() -> None:
    review = _human_review(as_of=AS_OF)
    result = evaluate_ade_from_parts(human_review=review, as_of=AS_OF_OTHER)
    assert result.outcome_kind is AdeOutcomeKind.EXPLICIT_ABSTENTION
    assert result.reason_family is AdeReasonFamily.TEMPORAL_PIT_MISMATCH
    assert result.decision_id is None


def test_naive_as_of_rejected() -> None:
    review = _human_review()
    with pytest.raises((ValidationError, AdeUnauthorizedInputError)):
        evaluate_ade(
            AdeEvaluationRequest(
                human_review=review,
                as_of=datetime(2026, 7, 17, 14, 0, 0),
            )
        )


def test_determinism_identical_inputs() -> None:
    review = _human_review()
    request = AdeEvaluationRequest(human_review=review, as_of=AS_OF, config=AdeConfig())
    first = evaluate_ade(request)
    second = evaluate_ade(request)
    third = reevaluate(request)
    assert first.model_dump(mode="python") == second.model_dump(mode="python")
    assert_replay_equal(first, third)
    assert first.decision_id == second.decision_id


def test_identity_stable_and_non_aliasing_across_as_of() -> None:
    review_a = _human_review(as_of=AS_OF)
    # Distinct attestation meaning under same as_of changes identity.
    review_b = _human_review(as_of=AS_OF, attestation="recorded-human-authority-v1-alt")
    id_a = build_ade_decision_id(human_review=review_a, config=AdeConfig())
    id_b = build_ade_decision_id(human_review=review_b, config=AdeConfig())
    assert id_a != id_b
    result_a = evaluate_ade_from_parts(human_review=review_a, as_of=AS_OF)
    result_b = evaluate_ade_from_parts(human_review=review_b, as_of=AS_OF)
    assert result_a.decision_id == id_a
    assert result_b.decision_id == id_b
    assert result_a.decision_id != result_b.decision_id


def test_abstention_has_no_canonical_decision_identity() -> None:
    result = evaluate_ade_from_parts(human_review=None, as_of=AS_OF)
    assert result.outcome_kind is AdeOutcomeKind.EXPLICIT_ABSTENTION
    assert result.decision_id is None


def test_reason_families_are_frozen_set_only() -> None:
    assert AdeReasonFamily.ACCEPTED_GOVERNED_EVIDENCE.value in FROZEN_REASON_FAMILIES
    assert len(FROZEN_REASON_FAMILIES) == 10
    with pytest.raises(ValidationError):
        AdeResult.model_validate(
            {
                "outcome_kind": AdeOutcomeKind.EXPLICIT_ABSTENTION,
                "policy_version_id": POLICY_VERSION_V1,
                "as_of": AS_OF,
                "reason_family": "invented_reason_family",
                "decision_id": None,
                "human_review_output_id": None,
                "provenance": evaluate_ade_from_parts(
                    human_review=None, as_of=AS_OF
                ).provenance.model_dump(mode="python"),
            }
        )


def test_invalid_policy_context_fail_closed() -> None:
    review = _human_review()
    with pytest.raises(ValidationError):
        AdeConfig(policy_version_id="ai-decision-engine.policy.v999")
    # Constructed request with wrong policy is blocked by AdeConfig validation.
    result = evaluate_ade_from_parts(human_review=review, as_of=AS_OF, config=AdeConfig())
    assert result.policy_version_id == POLICY_VERSION_V1


def test_conflicting_evidence_abstention() -> None:
    review = _human_review()
    conflicting = review.model_copy(
        update={"history": review.history.model_copy(update={"human_review_output_id": "f" * 64})}
    )
    result = evaluate_ade_from_parts(human_review=conflicting, as_of=AS_OF)
    assert result.outcome_kind is AdeOutcomeKind.EXPLICIT_ABSTENTION
    assert result.reason_family is AdeReasonFamily.CONFLICTING_OR_AMBIGUOUS_EVIDENCE


def test_stale_nested_record_uses_pit_not_ttl() -> None:
    review = _human_review()
    stale_record = review.records[0].model_copy(update={"scoring_as_of": AS_OF - timedelta(days=1)})
    stale_review = review.model_copy(update={"records": (stale_record,)})
    result = evaluate_ade_from_parts(human_review=stale_review, as_of=AS_OF)
    assert result.outcome_kind is AdeOutcomeKind.EXPLICIT_ABSTENTION
    assert result.reason_family is AdeReasonFamily.STALE_EVIDENCE


def test_invalid_attestation_abstention() -> None:
    review = _human_review()
    empty = review.model_copy(
        update={"attestation": review.attestation.model_copy(update={"recorded_payload": "   "})}
    )
    result = evaluate_ade_from_parts(human_review=empty, as_of=AS_OF)
    assert result.outcome_kind is AdeOutcomeKind.EXPLICIT_ABSTENTION
    assert result.reason_family is AdeReasonFamily.INVALID_AUTHORIZED_EVIDENCE


def test_identity_insufficiency_abstention() -> None:
    review = _human_review()
    broken = review.model_copy(update={"human_review_output_id": "not-a-sha256"})
    result = evaluate_ade_from_parts(human_review=broken, as_of=AS_OF)
    assert result.outcome_kind is AdeOutcomeKind.EXPLICIT_ABSTENTION
    assert result.reason_family is AdeReasonFamily.IDENTITY_INSUFFICIENCY


def test_provenance_insufficiency_abstention() -> None:
    review = _human_review()
    broken = review.model_copy(
        update={
            "provenance": review.provenance.model_copy(
                update={"provenance_specification_id": "wrong.provenance"}
            )
        }
    )
    result = evaluate_ade_from_parts(human_review=broken, as_of=AS_OF)
    assert result.outcome_kind is AdeOutcomeKind.EXPLICIT_ABSTENTION
    assert result.reason_family is AdeReasonFamily.PROVENANCE_INSUFFICIENCY


def test_model_participation_rejected() -> None:
    with pytest.raises(AdeModelParticipationError):
        evaluate_ade(
            {
                "human_review": None,
                "as_of": AS_OF.isoformat(),
                "model_output": {"text": "should not participate"},
            }
        )
    assert MODEL_PARTICIPATION == "UNAUTHORIZED"


def test_unauthorized_non_hr_input_rejected() -> None:
    with pytest.raises(AdeUnauthorizedInputError):
        evaluate_ade_from_parts(human_review={"not": "human_review"}, as_of=AS_OF)  # type: ignore[arg-type]


def test_replay_inequality_detected() -> None:
    review_a = _human_review(attestation="attestation-a")
    review_b = _human_review(attestation="attestation-b")
    first = evaluate_ade_from_parts(human_review=review_a, as_of=AS_OF)
    second = evaluate_ade_from_parts(human_review=review_b, as_of=AS_OF)
    with pytest.raises(AdeReplayInequalityError):
        assert_replay_equal(first, second)


def test_abstention_is_not_no_trade_or_human_rejection() -> None:
    result = evaluate_ade_from_parts(human_review=None, as_of=AS_OF)
    dumped = result.model_dump(mode="python")
    serialized = str(dumped).lower()
    assert "no_trade" not in serialized
    assert "buy" not in serialized
    assert "sell" not in serialized
    assert result.outcome_kind is AdeOutcomeKind.EXPLICIT_ABSTENTION
    assert result.outcome_kind.value != "no_trade"


def test_no_wall_clock_in_package_sources() -> None:
    root = Path(__file__).resolve().parents[2] / "app" / "ai_decision_engine"
    forbidden = ("datetime.now(", "datetime.utcnow(", "time.time(", "date.today(")
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{path} contains {token}"
