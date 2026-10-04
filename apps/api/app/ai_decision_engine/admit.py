"""Human Review public-output admission for ADE evaluation."""

from __future__ import annotations

from datetime import datetime

from pydantic import ValidationError

from app.ai_decision_engine.errors import AdeModelParticipationError, AdeUnauthorizedInputError
from app.ai_decision_engine.models import AdeEvaluationRequest
from app.ai_decision_engine.policy import (
    REQUIRED_UPSTREAM_HUMAN_REVIEW_IDENTITY_SPECIFICATION_ID,
    REQUIRED_UPSTREAM_HUMAN_REVIEW_POLICY_VERSION_ID,
    REQUIRED_UPSTREAM_HUMAN_REVIEW_PROVENANCE_SPECIFICATION_ID,
)
from app.ai_decision_engine.reasons import AdeReasonFamily
from app.human_review import POLICY_VERSION_V1 as HR_POLICY_VERSION_V1
from app.human_review import HumanReviewOutput
from app.market_data.timing import require_utc_aware


def _is_sha256_hex(value: str) -> bool:
    text = value.strip().lower()
    return len(text) == 64 and all(ch in "0123456789abcdef" for ch in text)


def coerce_evaluation_request(request: AdeEvaluationRequest | object) -> AdeEvaluationRequest:
    """Admit only ADE evaluation requests; reject unauthorized shapes at the boundary."""
    if isinstance(request, AdeEvaluationRequest):
        return request
    if isinstance(request, dict) and any(
        key in request
        for key in (
            "model_output",
            "model_response",
            "prompt",
            "llm",
            "provider",
            "confidence",
            "embedding",
        )
    ):
        raise AdeModelParticipationError(detail="unsupported_model_participation")
    try:
        return AdeEvaluationRequest.model_validate(request)
    except ValidationError as exc:
        raise AdeUnauthorizedInputError(detail=f"invalid_request:{exc}") from exc


def classify_admission(
    request: AdeEvaluationRequest,
) -> AdeReasonFamily | None:
    """
    Return a fail-closed reason family when HR public evidence is inadmissible.

    ``None`` means evidence is admissible for governed acceptance.
    """
    try:
        as_of = require_utc_aware(request.as_of, field_name="as_of")
    except ValueError:
        return AdeReasonFamily.TEMPORAL_PIT_MISMATCH

    human_review = request.human_review
    if human_review is None:
        return AdeReasonFamily.MISSING_AUTHORIZED_EVIDENCE
    if not isinstance(human_review, HumanReviewOutput):
        return AdeReasonFamily.INVALID_AUTHORIZED_EVIDENCE

    if human_review.policy_version_id != REQUIRED_UPSTREAM_HUMAN_REVIEW_POLICY_VERSION_ID:
        return AdeReasonFamily.INVALID_AUTHORIZED_EVIDENCE
    if human_review.policy_version_id != HR_POLICY_VERSION_V1:
        return AdeReasonFamily.INVALID_AUTHORIZED_EVIDENCE

    if not _is_sha256_hex(human_review.human_review_output_id):
        return AdeReasonFamily.IDENTITY_INSUFFICIENCY

    provenance = human_review.provenance
    if provenance.policy_version_id != REQUIRED_UPSTREAM_HUMAN_REVIEW_POLICY_VERSION_ID:
        return AdeReasonFamily.PROVENANCE_INSUFFICIENCY
    if provenance.identity_specification_id != (
        REQUIRED_UPSTREAM_HUMAN_REVIEW_IDENTITY_SPECIFICATION_ID
    ):
        return AdeReasonFamily.PROVENANCE_INSUFFICIENCY
    if provenance.provenance_specification_id != (
        REQUIRED_UPSTREAM_HUMAN_REVIEW_PROVENANCE_SPECIFICATION_ID
    ):
        return AdeReasonFamily.PROVENANCE_INSUFFICIENCY
    if not _is_sha256_hex(provenance.config_fingerprint):
        return AdeReasonFamily.PROVENANCE_INSUFFICIENCY
    if not _is_sha256_hex(provenance.input_fingerprint):
        return AdeReasonFamily.PROVENANCE_INSUFFICIENCY
    if not _is_sha256_hex(provenance.recorded_attestation_fingerprint):
        return AdeReasonFamily.PROVENANCE_INSUFFICIENCY

    attestation = human_review.attestation
    if not str(attestation.recorded_payload).strip():
        return AdeReasonFamily.INVALID_AUTHORIZED_EVIDENCE

    try:
        hr_as_of = require_utc_aware(human_review.as_of, field_name="human_review.as_of")
        prov_as_of = require_utc_aware(provenance.as_of, field_name="human_review.provenance.as_of")
    except ValueError:
        return AdeReasonFamily.TEMPORAL_PIT_MISMATCH

    # Frozen PIT semantics only — no invented TTL/freshness window.
    if as_of != hr_as_of or as_of != prov_as_of:
        return AdeReasonFamily.TEMPORAL_PIT_MISMATCH

    if human_review.identity_specification_id != (
        REQUIRED_UPSTREAM_HUMAN_REVIEW_IDENTITY_SPECIFICATION_ID
    ):
        return AdeReasonFamily.IDENTITY_INSUFFICIENCY
    if human_review.provenance_specification_id != (
        REQUIRED_UPSTREAM_HUMAN_REVIEW_PROVENANCE_SPECIFICATION_ID
    ):
        return AdeReasonFamily.PROVENANCE_INSUFFICIENCY

    conflict_or_stale = _classify_conflict_or_stale(human_review, as_of=as_of)
    if conflict_or_stale is not None:
        return conflict_or_stale

    return None


def _classify_conflict_or_stale(
    human_review: HumanReviewOutput,
    *,
    as_of: datetime,
) -> AdeReasonFamily | None:
    """Detect conflicting/ambiguous or PIT-inadmissible nested evidence."""
    if human_review.human_review_output_id != human_review.history.human_review_output_id:
        return AdeReasonFamily.CONFLICTING_OR_AMBIGUOUS_EVIDENCE
    if human_review.dashboard_output_id != human_review.provenance.upstream_dashboard_output_id:
        return AdeReasonFamily.CONFLICTING_OR_AMBIGUOUS_EVIDENCE
    if human_review.history.as_of != as_of:
        return AdeReasonFamily.TEMPORAL_PIT_MISMATCH

    seen_ids: set[str] = set()
    for record in human_review.records:
        if record.score_record_id in seen_ids:
            return AdeReasonFamily.CONFLICTING_OR_AMBIGUOUS_EVIDENCE
        seen_ids.add(record.score_record_id)
        try:
            record_as_of = require_utc_aware(record.scoring_as_of, field_name="scoring_as_of")
        except ValueError:
            return AdeReasonFamily.TEMPORAL_PIT_MISMATCH
        if record_as_of != as_of:
            # Nested lineage PIT-inadmissible under evaluation as_of (no TTL).
            return AdeReasonFamily.STALE_EVIDENCE
    return None
