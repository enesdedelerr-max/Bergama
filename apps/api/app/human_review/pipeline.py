"""Deterministic Human Review Pipeline."""

from __future__ import annotations

from app.human_review.errors import HumanReviewPipelineIsolationError
from app.human_review.history import build_history_binding
from app.human_review.identity import build_human_review_output_id
from app.human_review.models import HumanReviewOutput, HumanReviewUpstreamReferenceRecord
from app.human_review.ordering import preserve_dashboard_order
from app.human_review.output import to_human_review_output, to_upstream_record
from app.human_review.provenance import build_human_review_provenance
from app.human_review.validate_input import ValidatedHumanReviewRequest
from app.human_review.validate_output import validate_human_review_output


def run_human_review_pipeline(request: ValidatedHumanReviewRequest) -> HumanReviewOutput:
    """Execute the immutable Policy Version v1 Human Review Pipeline once.

    Stage order is immutable:
    1. Input Validation (already applied)
    2. Policy Version Binding (already applied)
    3. Configuration Binding (already applied)
    4. PIT Validation (already applied)
    5. Authorized Input Admission (already applied)
    6. Explicit Human Attestation Admission (already applied)
    7. Dashboard Reference Preservation
    8. Ordering Preservation
    9. Human Review Record Construction
    10. Human Review Identity Generation
    11. Human Review Provenance Generation
    12. Review History Binding
    13. Output Construction
    14. Post-Validation
    15. Emission
    """
    if not isinstance(request, ValidatedHumanReviewRequest):
        raise HumanReviewPipelineIsolationError(detail="unvalidated_request")

    # Stage 7 — Dashboard Reference Preservation (read-only capture)
    dashboard = request.dashboard
    dashboard_policy_version_id = dashboard.policy_version_id

    # Stage 8 — Ordering Preservation
    ordered_pairs = preserve_dashboard_order(dashboard)

    # Stage 9 — Human Review Record Construction
    records: list[HumanReviewUpstreamReferenceRecord] = []
    for sequence_index, dashboard_record in ordered_pairs:
        records.append(
            to_upstream_record(
                sequence_index=sequence_index,
                dashboard_record=dashboard_record,
                dashboard_policy_version_id=dashboard_policy_version_id,
            )
        )
    preserved_records = tuple(records)

    # Stage 10 — Human Review Identity Generation
    human_review_output_id = build_human_review_output_id(request)

    # Stage 11 — Human Review Provenance Generation
    provenance = build_human_review_provenance(request)

    # Stage 12 — Review History Binding
    history = build_history_binding(
        human_review_output_id=human_review_output_id,
        request=request,
        provenance=provenance,
    )

    # Stage 13 — Output Construction
    output = to_human_review_output(
        human_review_output_id=human_review_output_id,
        as_of=request.as_of,
        dashboard_output_id=dashboard.dashboard_output_id,
        records=preserved_records,
        attestation=request.attestation,
        provenance=provenance,
        history=history,
    )

    # Stage 14 — Post-Validation
    validated = validate_human_review_output(output, request=request)

    # Stage 15 — Emission (exactly one complete output)
    return validated
