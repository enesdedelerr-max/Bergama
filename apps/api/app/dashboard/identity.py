"""Identity Specification ``dashboard.identity.v1``."""

from __future__ import annotations

from app.dashboard.errors import DashboardUnsupportedPolicyError
from app.dashboard.models import DashboardConfig
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


def build_dashboard_output_id(request: ValidatedDashboardRequest) -> str:
    """Return sha256 hex Dashboard identity over the canonical v1 payload."""
    if request.config.digest_method_id != DIGEST_METHOD_V1:
        raise DashboardUnsupportedPolicyError(
            detail=f"unsupported_digest_method:{request.config.digest_method_id}"
        )
    return strategy_sha256(_canonical_identity_payload(request))


def _canonical_identity_payload(request: ValidatedDashboardRequest) -> dict[str, object]:
    config: DashboardConfig = request.config
    return {
        "schema": IDENTITY_SPECIFICATION_V1,
        "policy_version_id": POLICY_VERSION_V1,
        "ordering_preservation_policy_id": ORDERING_PRESERVATION_POLICY_V1,
        "presentation_selection_policy_id": PRESENTATION_SELECTION_POLICY_V1,
        "provenance_specification_id": PROVENANCE_SPECIFICATION_V1,
        "as_of": request.as_of,
        "configuration": config.model_dump(mode="python"),
        "ordered_score_record_ids": [record.score_record_id for record in request.briefing.records],
        "upstream_briefing_id": request.briefing.briefing_id,
        "upstream_briefing_provenance": request.briefing.provenance.model_dump(mode="python"),
    }
