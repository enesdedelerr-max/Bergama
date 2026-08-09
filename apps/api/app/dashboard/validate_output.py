"""Post-condition Validation Layer for Dashboard."""

from __future__ import annotations

from decimal import Decimal

from app.dashboard.errors import (
    DashboardConfigurationError,
    DashboardDomainError,
    DashboardIdentityError,
    DashboardInvariantError,
    DashboardOrderingError,
    DashboardOutputCompletenessError,
    DashboardProvenanceError,
)
from app.dashboard.identity import build_dashboard_output_id
from app.dashboard.models import DashboardPresentationOutput
from app.dashboard.ordering import assert_ordering_preserved
from app.dashboard.policy import (
    DIGEST_METHOD_V1,
    IDENTITY_SPECIFICATION_V1,
    ORDERING_PRESERVATION_POLICY_V1,
    POLICY_VERSION_V1,
    PRESENTATION_SELECTION_POLICY_V1,
    PROVENANCE_SPECIFICATION_V1,
    REQUIRED_UPSTREAM_BRIEFING_POLICY_VERSION_ID,
)
from app.dashboard.provenance import build_dashboard_provenance
from app.dashboard.validate_input import ValidatedDashboardRequest


def validate_dashboard_output(
    output: DashboardPresentationOutput,
    *,
    request: ValidatedDashboardRequest,
) -> DashboardPresentationOutput:
    """Enforce Policy Version v1 post-conditions before emission."""
    if output.as_of != request.as_of:
        raise DashboardInvariantError(detail="as_of_mismatch")
    if output.policy_version_id != POLICY_VERSION_V1:
        raise DashboardInvariantError(detail="policy_version_mismatch")
    if output.ordering_preservation_policy_id != ORDERING_PRESERVATION_POLICY_V1:
        raise DashboardInvariantError(detail="ordering_preservation_policy_mismatch")
    if output.presentation_selection_policy_id != PRESENTATION_SELECTION_POLICY_V1:
        raise DashboardInvariantError(detail="presentation_selection_policy_mismatch")
    if request.config.policy_version_id != POLICY_VERSION_V1:
        raise DashboardConfigurationError(detail="bound_config_policy_mismatch")
    if request.config.digest_method_id != DIGEST_METHOD_V1:
        raise DashboardConfigurationError(detail="digest_method_mismatch")

    provenance = output.provenance
    if provenance.policy_version_id != POLICY_VERSION_V1:
        raise DashboardProvenanceError(detail="provenance_policy_version_mismatch")
    if provenance.ordering_preservation_policy_id != ORDERING_PRESERVATION_POLICY_V1:
        raise DashboardProvenanceError(detail="provenance_ordering_policy_mismatch")
    if provenance.presentation_selection_policy_id != PRESENTATION_SELECTION_POLICY_V1:
        raise DashboardProvenanceError(detail="provenance_presentation_selection_mismatch")
    if provenance.identity_specification_id != IDENTITY_SPECIFICATION_V1:
        raise DashboardProvenanceError(detail="identity_specification_mismatch")
    if provenance.provenance_specification_id != PROVENANCE_SPECIFICATION_V1:
        raise DashboardProvenanceError(detail="provenance_specification_mismatch")
    if provenance.digest_method_id != DIGEST_METHOD_V1:
        raise DashboardProvenanceError(detail="digest_method_mismatch")
    if provenance.as_of != request.as_of:
        raise DashboardProvenanceError(detail="provenance_as_of_mismatch")

    expected_provenance = build_dashboard_provenance(request)
    if provenance != expected_provenance:
        raise DashboardProvenanceError(detail="provenance_mismatch")

    expected_output_id = build_dashboard_output_id(request)
    if output.dashboard_output_id != expected_output_id:
        raise DashboardIdentityError(detail="dashboard_output_id_mismatch")
    if output.dashboard_output_id == request.briefing.briefing_id:
        raise DashboardIdentityError(detail="dashboard_output_id_reuses_briefing_id")

    assert_ordering_preserved(briefing=request.briefing, records=output.records)

    expected_source_ids = tuple(record.score_record_id for record in request.briefing.records)
    if provenance.source_identifiers != expected_source_ids:
        raise DashboardOrderingError(detail="source_identifiers_mismatch")
    if provenance.upstream_briefing_id != request.briefing.briefing_id:
        raise DashboardProvenanceError(detail="upstream_briefing_id_mismatch")
    if provenance.upstream_briefing_policy_version_id != (
        REQUIRED_UPSTREAM_BRIEFING_POLICY_VERSION_ID
    ):
        raise DashboardProvenanceError(detail="upstream_briefing_policy_mismatch")

    if len(output.records) != len(request.briefing.records):
        raise DashboardOutputCompletenessError(detail="record_count_mismatch")

    for index, (dashboard_record, briefing_record) in enumerate(
        zip(output.records, request.briefing.records, strict=True)
    ):
        if dashboard_record.local_symbol != briefing_record.local_symbol:
            raise DashboardInvariantError(detail=f"local_symbol_mutation:{index}")
        if dashboard_record.components != briefing_record.components:
            raise DashboardInvariantError(detail=f"components_mutation:{index}")
        if dashboard_record.scoring_policy_version_id != briefing_record.scoring_policy_version_id:
            raise DashboardInvariantError(detail=f"scoring_policy_mutation:{index}")
        if dashboard_record.scoring_weight_profile_id != briefing_record.scoring_weight_profile_id:
            raise DashboardInvariantError(detail=f"scoring_weight_mutation:{index}")
        if dashboard_record.scoring_as_of != briefing_record.scoring_as_of:
            raise DashboardInvariantError(detail=f"scoring_as_of_mutation:{index}")
        if dashboard_record.watchlist_rank != briefing_record.watchlist_rank:
            raise DashboardInvariantError(detail=f"watchlist_rank_mutation:{index}")
        if dashboard_record.watchlist_rule_id != briefing_record.watchlist_rule_id:
            raise DashboardInvariantError(detail=f"watchlist_rule_id_mutation:{index}")
        if dashboard_record.gap_record_id != briefing_record.gap_record_id:
            raise DashboardInvariantError(detail=f"gap_record_id_mutation:{index}")
        if dashboard_record.catalyst_source_identifiers != (
            briefing_record.catalyst_source_identifiers
        ):
            raise DashboardInvariantError(detail=f"catalyst_source_identifiers_mutation:{index}")
        if (
            dashboard_record.morning_briefing_policy_version_id
            != REQUIRED_UPSTREAM_BRIEFING_POLICY_VERSION_ID
        ):
            raise DashboardInvariantError(detail=f"morning_briefing_policy_mutation:{index}")
        if not dashboard_record.score.is_finite():
            raise DashboardDomainError(detail=f"non_finite_score:{dashboard_record.instrument_key}")
        if dashboard_record.score < Decimal("0") or dashboard_record.score > Decimal("1"):
            raise DashboardDomainError(
                detail=f"score_out_of_domain:{dashboard_record.instrument_key}"
            )
        if dashboard_record.score_record_id == output.dashboard_output_id:
            raise DashboardIdentityError(detail="dashboard_output_id_reuses_score_record_id")

    return output
