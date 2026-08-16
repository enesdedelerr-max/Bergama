"""Provenance Specification ``human-review.provenance.v1``."""

from __future__ import annotations

from app.human_review.errors import HumanReviewUnsupportedPolicyError
from app.human_review.identity import recorded_attestation_fingerprint
from app.human_review.models import HumanReviewProvenance
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


def build_config_fingerprint(request: ValidatedHumanReviewRequest) -> str:
    """Deterministic fingerprint of configuration and Policy Version binding."""
    if request.config.digest_method_id != DIGEST_METHOD_V1:
        raise HumanReviewUnsupportedPolicyError(
            detail=f"unsupported_digest_method:{request.config.digest_method_id}"
        )
    return strategy_sha256(
        {
            "config": request.config.model_dump(mode="python"),
            "policy_version_id": POLICY_VERSION_V1,
            "ordering_preservation_policy_id": ORDERING_PRESERVATION_POLICY_V1,
            "presentation_preservation_policy_id": PRESENTATION_PRESERVATION_POLICY_V1,
            "human_attestation_policy_id": HUMAN_ATTESTATION_POLICY_V1,
            "identity_specification_id": IDENTITY_SPECIFICATION_V1,
            "provenance_specification_id": PROVENANCE_SPECIFICATION_V1,
            "history_specification_id": HISTORY_SPECIFICATION_V1,
            "digest_method_id": DIGEST_METHOD_V1,
        }
    )


def build_input_fingerprint(request: ValidatedHumanReviewRequest) -> str:
    """Deterministic fingerprint of authorized inputs actually consumed."""
    dashboard = request.dashboard
    upstream = dashboard.provenance
    return strategy_sha256(
        {
            "as_of": request.as_of,
            "ordered_score_record_ids": [record.score_record_id for record in dashboard.records],
            "upstream_dashboard_output_id": dashboard.dashboard_output_id,
            "upstream_dashboard_provenance": upstream.model_dump(mode="python"),
            "upstream_dashboard_policy_version_id": dashboard.policy_version_id,
            "ordering_preservation_policy_id": ORDERING_PRESERVATION_POLICY_V1,
            "recorded_attestation_fingerprint": recorded_attestation_fingerprint(
                request.attestation
            ),
        }
    )


def build_human_review_provenance(request: ValidatedHumanReviewRequest) -> HumanReviewProvenance:
    """Build evaluation-level Human Review provenance."""
    dashboard = request.dashboard
    upstream = dashboard.provenance
    source_identifiers = tuple(record.score_record_id for record in dashboard.records)
    return HumanReviewProvenance(
        policy_version_id=POLICY_VERSION_V1,
        ordering_preservation_policy_id=ORDERING_PRESERVATION_POLICY_V1,
        presentation_preservation_policy_id=PRESENTATION_PRESERVATION_POLICY_V1,
        human_attestation_policy_id=HUMAN_ATTESTATION_POLICY_V1,
        identity_specification_id=IDENTITY_SPECIFICATION_V1,
        provenance_specification_id=PROVENANCE_SPECIFICATION_V1,
        history_specification_id=HISTORY_SPECIFICATION_V1,
        digest_method_id=DIGEST_METHOD_V1,
        as_of=request.as_of,
        config_fingerprint=build_config_fingerprint(request),
        input_fingerprint=build_input_fingerprint(request),
        source_identifiers=source_identifiers,
        upstream_dashboard_output_id=dashboard.dashboard_output_id,
        upstream_dashboard_policy_version_id=dashboard.policy_version_id,
        upstream_dashboard_identity_specification_id=upstream.identity_specification_id,
        upstream_dashboard_provenance_specification_id=upstream.provenance_specification_id,
        upstream_dashboard_config_fingerprint=upstream.config_fingerprint,
        upstream_dashboard_input_fingerprint=upstream.input_fingerprint,
        recorded_attestation_fingerprint=recorded_attestation_fingerprint(request.attestation),
    )
