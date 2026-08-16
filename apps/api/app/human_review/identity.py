"""Identity Specification ``human-review.identity.v1``."""

from __future__ import annotations

from app.human_review.errors import HumanReviewUnsupportedPolicyError
from app.human_review.models import HumanReviewConfig, HumanReviewRecordedAttestation
from app.human_review.policy import (
    DIGEST_METHOD_V1,
    HISTORY_SPECIFICATION_V1,
    HUMAN_ATTESTATION_POLICY_V1,
    IDENTITY_SPECIFICATION_V1,
    ORDERING_PRESERVATION_POLICY_V1,
    POLICY_VERSION_V1,
    PRESENTATION_PRESERVATION_POLICY_V1,
    PROVENANCE_SPECIFICATION_V1,
)
from app.human_review.validate_input import ValidatedHumanReviewRequest
from app.strategy.keys import strategy_sha256


def recorded_attestation_fingerprint(attestation: HumanReviewRecordedAttestation) -> str:
    """Deterministic fingerprint of the admitted recorded attestation payload."""
    return strategy_sha256({"recorded_payload": attestation.recorded_payload})


def build_human_review_output_id(request: ValidatedHumanReviewRequest) -> str:
    """Return sha256 hex Human Review identity over the canonical v1 payload."""
    if request.config.digest_method_id != DIGEST_METHOD_V1:
        raise HumanReviewUnsupportedPolicyError(
            detail=f"unsupported_digest_method:{request.config.digest_method_id}"
        )
    return strategy_sha256(_canonical_identity_payload(request))


def _canonical_identity_payload(request: ValidatedHumanReviewRequest) -> dict[str, object]:
    config: HumanReviewConfig = request.config
    dashboard = request.dashboard
    return {
        "schema": IDENTITY_SPECIFICATION_V1,
        "policy_version_id": POLICY_VERSION_V1,
        "ordering_preservation_policy_id": ORDERING_PRESERVATION_POLICY_V1,
        "presentation_preservation_policy_id": PRESENTATION_PRESERVATION_POLICY_V1,
        "human_attestation_policy_id": HUMAN_ATTESTATION_POLICY_V1,
        "provenance_specification_id": PROVENANCE_SPECIFICATION_V1,
        "history_specification_id": HISTORY_SPECIFICATION_V1,
        "as_of": request.as_of,
        "configuration": config.model_dump(mode="python"),
        "ordered_score_record_ids": [record.score_record_id for record in dashboard.records],
        "upstream_dashboard_output_id": dashboard.dashboard_output_id,
        "upstream_dashboard_provenance": dashboard.provenance.model_dump(mode="python"),
        "recorded_attestation_fingerprint": recorded_attestation_fingerprint(request.attestation),
    }
