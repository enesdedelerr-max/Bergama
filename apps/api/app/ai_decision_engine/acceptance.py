"""Deterministic governed acceptance under Policy Version v1."""

from __future__ import annotations

from app.ai_decision_engine.admit import classify_admission
from app.ai_decision_engine.identity import build_ade_decision_id
from app.ai_decision_engine.models import AdeEvaluationRequest, AdeOutcomeKind, AdeResult
from app.ai_decision_engine.policy import POLICY_VERSION_V1
from app.ai_decision_engine.provenance import build_ade_provenance
from app.ai_decision_engine.reasons import AdeReasonFamily
from app.human_review import HumanReviewOutput


def evaluate_governed_acceptance(request: AdeEvaluationRequest) -> AdeResult:
    """
    Establish authoritative ADE decision or explicit abstention.

    Canonical ADE authority exists only when frozen acceptance conditions hold.
    Otherwise the governed outcome is explicit abstention (fail closed).
    """
    if request.config.policy_version_id != POLICY_VERSION_V1:
        return _abstain(
            request,
            reason=AdeReasonFamily.POLICY_CONTEXT_INSUFFICIENCY,
            detail="policy_context_insufficiency",
        )

    admission_reason = classify_admission(request)
    if admission_reason is not None:
        return _abstain(request, reason=admission_reason, detail=admission_reason.value)

    human_review = request.human_review
    if not isinstance(human_review, HumanReviewOutput):
        return _abstain(
            request,
            reason=AdeReasonFamily.DETERMINISTIC_ACCEPTANCE_NOT_ESTABLISHED,
            detail="acceptance_not_established",
        )

    try:
        decision_id = build_ade_decision_id(human_review=human_review, config=request.config)
    except ValueError:
        return _abstain(
            request,
            reason=AdeReasonFamily.IDENTITY_INSUFFICIENCY,
            detail="identity_insufficiency",
        )

    provenance = build_ade_provenance(
        human_review=human_review,
        as_of=request.as_of,
        config=request.config,
    )
    return AdeResult(
        outcome_kind=AdeOutcomeKind.AUTHORITATIVE_DECISION,
        policy_version_id=POLICY_VERSION_V1,
        as_of=request.as_of,
        reason_family=AdeReasonFamily.ACCEPTED_GOVERNED_EVIDENCE,
        decision_id=decision_id,
        human_review_output_id=human_review.human_review_output_id,
        provenance=provenance,
        detail="accepted_governed_evidence",
    )


def _abstain(
    request: AdeEvaluationRequest,
    *,
    reason: AdeReasonFamily,
    detail: str,
) -> AdeResult:
    human_review = (
        request.human_review if isinstance(request.human_review, HumanReviewOutput) else None
    )
    provenance = build_ade_provenance(
        human_review=human_review,
        as_of=request.as_of,
        config=request.config,
    )
    return AdeResult(
        outcome_kind=AdeOutcomeKind.EXPLICIT_ABSTENTION,
        policy_version_id=POLICY_VERSION_V1,
        as_of=request.as_of,
        reason_family=reason,
        decision_id=None,
        human_review_output_id=(
            request.human_review.human_review_output_id
            if isinstance(request.human_review, HumanReviewOutput)
            and _safe_hex(request.human_review.human_review_output_id)
            else None
        ),
        provenance=provenance,
        detail=detail,
    )


def _safe_hex(value: str) -> bool:
    text = value.strip().lower()
    return len(text) == 64 and all(ch in "0123456789abcdef" for ch in text)
