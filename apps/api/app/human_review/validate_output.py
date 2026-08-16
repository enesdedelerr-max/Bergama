"""Post-condition Validation Layer for Human Review."""

from __future__ import annotations

from decimal import Decimal

from app.human_review.errors import (
    HumanReviewConfigurationError,
    HumanReviewDomainError,
    HumanReviewHistoryError,
    HumanReviewIdentityError,
    HumanReviewInvariantError,
    HumanReviewOrderingError,
    HumanReviewOutputCompletenessError,
    HumanReviewProvenanceError,
)
from app.human_review.history import build_history_binding
from app.human_review.identity import build_human_review_output_id, recorded_attestation_fingerprint
from app.human_review.models import HumanReviewOutput
from app.human_review.ordering import assert_ordering_preserved
from app.human_review.policy import (
    DIGEST_METHOD_V1,
    HISTORY_SPECIFICATION_V1,
    HUMAN_ATTESTATION_POLICY_V1,
    IDENTITY_SPECIFICATION_V1,
    ORDERING_PRESERVATION_POLICY_V1,
    POLICY_VERSION_V1,
    PRESENTATION_PRESERVATION_POLICY_V1,
    PROVENANCE_SPECIFICATION_V1,
    REQUIRED_UPSTREAM_DASHBOARD_POLICY_VERSION_ID,
)
from app.human_review.provenance import build_human_review_provenance
from app.human_review.validate_input import ValidatedHumanReviewRequest


def validate_human_review_output(
    output: HumanReviewOutput,
    *,
    request: ValidatedHumanReviewRequest,
) -> HumanReviewOutput:
    """Enforce Policy Version v1 post-conditions before emission."""
    if output.as_of != request.as_of:
        raise HumanReviewInvariantError(detail="as_of_mismatch")
    if output.policy_version_id != POLICY_VERSION_V1:
        raise HumanReviewInvariantError(detail="policy_version_mismatch")
    if output.ordering_preservation_policy_id != ORDERING_PRESERVATION_POLICY_V1:
        raise HumanReviewInvariantError(detail="ordering_preservation_policy_mismatch")
    if output.presentation_preservation_policy_id != PRESENTATION_PRESERVATION_POLICY_V1:
        raise HumanReviewInvariantError(detail="presentation_preservation_policy_mismatch")
    if output.human_attestation_policy_id != HUMAN_ATTESTATION_POLICY_V1:
        raise HumanReviewInvariantError(detail="human_attestation_policy_mismatch")
    if output.identity_specification_id != IDENTITY_SPECIFICATION_V1:
        raise HumanReviewInvariantError(detail="identity_specification_mismatch")
    if output.provenance_specification_id != PROVENANCE_SPECIFICATION_V1:
        raise HumanReviewInvariantError(detail="provenance_specification_mismatch")
    if output.history_specification_id != HISTORY_SPECIFICATION_V1:
        raise HumanReviewInvariantError(detail="history_specification_mismatch")
    if request.config.policy_version_id != POLICY_VERSION_V1:
        raise HumanReviewConfigurationError(detail="bound_config_policy_mismatch")
    if request.config.digest_method_id != DIGEST_METHOD_V1:
        raise HumanReviewConfigurationError(detail="digest_method_mismatch")
    if output.attestation != request.attestation:
        raise HumanReviewInvariantError(detail="attestation_mismatch")

    provenance = output.provenance
    if provenance.policy_version_id != POLICY_VERSION_V1:
        raise HumanReviewProvenanceError(detail="provenance_policy_version_mismatch")
    if provenance.ordering_preservation_policy_id != ORDERING_PRESERVATION_POLICY_V1:
        raise HumanReviewProvenanceError(detail="provenance_ordering_policy_mismatch")
    if provenance.presentation_preservation_policy_id != PRESENTATION_PRESERVATION_POLICY_V1:
        raise HumanReviewProvenanceError(detail="provenance_presentation_preservation_mismatch")
    if provenance.human_attestation_policy_id != HUMAN_ATTESTATION_POLICY_V1:
        raise HumanReviewProvenanceError(detail="provenance_human_attestation_mismatch")
    if provenance.identity_specification_id != IDENTITY_SPECIFICATION_V1:
        raise HumanReviewProvenanceError(detail="identity_specification_mismatch")
    if provenance.provenance_specification_id != PROVENANCE_SPECIFICATION_V1:
        raise HumanReviewProvenanceError(detail="provenance_specification_mismatch")
    if provenance.history_specification_id != HISTORY_SPECIFICATION_V1:
        raise HumanReviewProvenanceError(detail="history_specification_mismatch")
    if provenance.digest_method_id != DIGEST_METHOD_V1:
        raise HumanReviewProvenanceError(detail="digest_method_mismatch")
    if provenance.as_of != request.as_of:
        raise HumanReviewProvenanceError(detail="provenance_as_of_mismatch")

    expected_provenance = build_human_review_provenance(request)
    if provenance != expected_provenance:
        raise HumanReviewProvenanceError(detail="provenance_mismatch")

    expected_output_id = build_human_review_output_id(request)
    if output.human_review_output_id != expected_output_id:
        raise HumanReviewIdentityError(detail="human_review_output_id_mismatch")
    if output.human_review_output_id == request.dashboard.dashboard_output_id:
        raise HumanReviewIdentityError(detail="human_review_output_id_reuses_dashboard_output_id")
    if output.human_review_output_id == request.dashboard.provenance.upstream_briefing_id:
        raise HumanReviewIdentityError(detail="human_review_output_id_reuses_briefing_id")

    expected_history = build_history_binding(
        human_review_output_id=expected_output_id,
        request=request,
        provenance=expected_provenance,
    )
    if output.history != expected_history:
        raise HumanReviewHistoryError(detail="history_mismatch")
    if output.history.human_review_output_id != output.human_review_output_id:
        raise HumanReviewHistoryError(detail="history_output_id_mismatch")
    if output.history.recorded_attestation_fingerprint != recorded_attestation_fingerprint(
        request.attestation
    ):
        raise HumanReviewHistoryError(detail="history_attestation_fingerprint_mismatch")

    assert_ordering_preserved(dashboard=request.dashboard, records=output.records)

    expected_source_ids = tuple(record.score_record_id for record in request.dashboard.records)
    if provenance.source_identifiers != expected_source_ids:
        raise HumanReviewOrderingError(detail="source_identifiers_mismatch")
    if provenance.upstream_dashboard_output_id != request.dashboard.dashboard_output_id:
        raise HumanReviewProvenanceError(detail="upstream_dashboard_output_id_mismatch")
    if provenance.upstream_dashboard_policy_version_id != (
        REQUIRED_UPSTREAM_DASHBOARD_POLICY_VERSION_ID
    ):
        raise HumanReviewProvenanceError(detail="upstream_dashboard_policy_mismatch")
    if output.dashboard_output_id != request.dashboard.dashboard_output_id:
        raise HumanReviewInvariantError(detail="dashboard_output_id_mismatch")

    if len(output.records) != len(request.dashboard.records):
        raise HumanReviewOutputCompletenessError(detail="record_count_mismatch")

    for index, (review_record, dashboard_record) in enumerate(
        zip(output.records, request.dashboard.records, strict=True)
    ):
        if review_record.local_symbol != dashboard_record.local_symbol:
            raise HumanReviewInvariantError(detail=f"local_symbol_mutation:{index}")
        if review_record.components != dashboard_record.components:
            raise HumanReviewInvariantError(detail=f"components_mutation:{index}")
        if review_record.scoring_as_of != dashboard_record.scoring_as_of:
            raise HumanReviewInvariantError(detail=f"scoring_as_of_mutation:{index}")
        if review_record.dashboard_policy_version_id != (
            REQUIRED_UPSTREAM_DASHBOARD_POLICY_VERSION_ID
        ):
            raise HumanReviewInvariantError(detail=f"dashboard_policy_mutation:{index}")
        if not review_record.score.is_finite():
            raise HumanReviewDomainError(detail=f"non_finite_score:{review_record.instrument_key}")
        if review_record.score < Decimal("0") or review_record.score > Decimal("1"):
            raise HumanReviewDomainError(
                detail=f"score_out_of_domain:{review_record.instrument_key}"
            )
        if review_record.score_record_id == output.human_review_output_id:
            raise HumanReviewIdentityError(detail="human_review_output_id_reuses_score_record_id")

    return output
