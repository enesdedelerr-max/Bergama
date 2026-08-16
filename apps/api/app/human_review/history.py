"""History Specification ``human-review.history.v1``."""

from __future__ import annotations

from app.human_review.identity import recorded_attestation_fingerprint
from app.human_review.models import HumanReviewHistoryBinding, HumanReviewProvenance
from app.human_review.policy import HISTORY_SPECIFICATION_V1
from app.human_review.validate_input import ValidatedHumanReviewRequest


def build_history_binding(
    *,
    human_review_output_id: str,
    request: ValidatedHumanReviewRequest,
    provenance: HumanReviewProvenance,
) -> HumanReviewHistoryBinding:
    """Bind reconstructable Human Review history for one evaluation."""
    dashboard = request.dashboard
    upstream = dashboard.provenance
    return HumanReviewHistoryBinding(
        human_review_output_id=human_review_output_id,
        history_specification_id=HISTORY_SPECIFICATION_V1,
        as_of=request.as_of,
        upstream_dashboard_output_id=dashboard.dashboard_output_id,
        upstream_dashboard_config_fingerprint=upstream.config_fingerprint,
        upstream_dashboard_input_fingerprint=upstream.input_fingerprint,
        recorded_attestation_fingerprint=recorded_attestation_fingerprint(request.attestation),
        provenance_config_fingerprint=provenance.config_fingerprint,
        provenance_input_fingerprint=provenance.input_fingerprint,
    )
