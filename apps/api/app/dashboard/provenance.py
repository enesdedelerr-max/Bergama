"""Provenance Specification ``dashboard.provenance.v1``."""

from __future__ import annotations

from app.dashboard.errors import DashboardUnsupportedPolicyError
from app.dashboard.models import DashboardProvenance
from app.dashboard.policy import (
    DIGEST_METHOD_V1,
    IDENTITY_SPECIFICATION_V1,
    ORDERING_PRESERVATION_POLICY_V1,
    POLICY_VERSION_V1,
    PRESENTATION_SELECTION_POLICY_V1,
    PROVENANCE_SPECIFICATION_V1,
)
from app.dashboard.validate_input import ValidatedDashboardRequest
from app.strategy.keys import strategy_sha256


def build_config_fingerprint(request: ValidatedDashboardRequest) -> str:
    """Deterministic fingerprint of configuration and Policy Version binding."""
    if request.config.digest_method_id != DIGEST_METHOD_V1:
        raise DashboardUnsupportedPolicyError(
            detail=f"unsupported_digest_method:{request.config.digest_method_id}"
        )
    return strategy_sha256(
        {
            "config": request.config.model_dump(mode="python"),
            "policy_version_id": POLICY_VERSION_V1,
            "ordering_preservation_policy_id": ORDERING_PRESERVATION_POLICY_V1,
            "presentation_selection_policy_id": PRESENTATION_SELECTION_POLICY_V1,
            "identity_specification_id": IDENTITY_SPECIFICATION_V1,
            "provenance_specification_id": PROVENANCE_SPECIFICATION_V1,
            "digest_method_id": DIGEST_METHOD_V1,
        }
    )


def build_input_fingerprint(request: ValidatedDashboardRequest) -> str:
    """Deterministic fingerprint of authorized inputs actually consumed."""
    return strategy_sha256(
        {
            "as_of": request.as_of,
            "ordered_score_record_ids": [
                record.score_record_id for record in request.briefing.records
            ],
            "upstream_briefing_id": request.briefing.briefing_id,
            "upstream_briefing_provenance": request.briefing.provenance.model_dump(mode="python"),
            "upstream_briefing_policy_version_id": request.briefing.policy_version_id,
            "ordering_preservation_policy_id": ORDERING_PRESERVATION_POLICY_V1,
        }
    )


def build_dashboard_provenance(request: ValidatedDashboardRequest) -> DashboardProvenance:
    """Build evaluation-level Dashboard provenance."""
    source_identifiers = tuple(record.score_record_id for record in request.briefing.records)
    upstream = request.briefing.provenance
    return DashboardProvenance(
        policy_version_id=POLICY_VERSION_V1,
        ordering_preservation_policy_id=ORDERING_PRESERVATION_POLICY_V1,
        presentation_selection_policy_id=PRESENTATION_SELECTION_POLICY_V1,
        identity_specification_id=IDENTITY_SPECIFICATION_V1,
        provenance_specification_id=PROVENANCE_SPECIFICATION_V1,
        digest_method_id=DIGEST_METHOD_V1,
        as_of=request.as_of,
        config_fingerprint=build_config_fingerprint(request),
        input_fingerprint=build_input_fingerprint(request),
        source_identifiers=source_identifiers,
        upstream_briefing_id=request.briefing.briefing_id,
        upstream_briefing_policy_version_id=request.briefing.policy_version_id,
        upstream_briefing_ordering_preservation_policy_id=(
            request.briefing.ordering_preservation_policy_id
        ),
        upstream_briefing_identity_specification_id=upstream.identity_specification_id,
        upstream_briefing_provenance_specification_id=upstream.provenance_specification_id,
        upstream_briefing_config_fingerprint=upstream.config_fingerprint,
        upstream_briefing_input_fingerprint=upstream.input_fingerprint,
    )
