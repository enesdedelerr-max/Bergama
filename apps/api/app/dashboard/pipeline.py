"""Deterministic Dashboard Presentation Pipeline."""

from __future__ import annotations

from app.dashboard.errors import DashboardPipelineIsolationError
from app.dashboard.identity import build_dashboard_output_id
from app.dashboard.models import DashboardPresentationOutput, DashboardPresentationRecord
from app.dashboard.ordering import preserve_morning_briefing_order
from app.dashboard.output import to_dashboard_output, to_dashboard_record
from app.dashboard.provenance import build_dashboard_provenance
from app.dashboard.validate_input import ValidatedDashboardRequest
from app.dashboard.validate_output import validate_dashboard_output


def run_dashboard_pipeline(request: ValidatedDashboardRequest) -> DashboardPresentationOutput:
    """Execute the immutable Policy Version v1 Presentation Pipeline once.

    Stage order is immutable:
    1. Input Validation (already applied)
    2. Policy Version Binding (already applied)
    3. Configuration Binding (already applied)
    4. PIT Validation (already applied)
    5. Authorized Input Admission (already applied)
    6. Morning Briefing Reference Preservation
    7. Ordering Preservation
    8. Dashboard Presentation Assembly
    9. Dashboard Identity Generation
    10. Dashboard Provenance Generation
    11. Output Construction
    12. Post-Validation
    13. Emission
    """
    if not isinstance(request, ValidatedDashboardRequest):
        raise DashboardPipelineIsolationError(detail="unvalidated_request")

    # Stage 6 — Morning Briefing Reference Preservation (read-only capture)
    briefing = request.briefing
    morning_briefing_policy_version_id = briefing.policy_version_id

    # Stage 7 — Ordering Preservation
    ordered_pairs = preserve_morning_briefing_order(briefing)

    # Stage 8 — Dashboard Presentation Assembly
    records: list[DashboardPresentationRecord] = []
    for sequence_index, briefing_record in ordered_pairs:
        records.append(
            to_dashboard_record(
                sequence_index=sequence_index,
                briefing_record=briefing_record,
                morning_briefing_policy_version_id=morning_briefing_policy_version_id,
            )
        )
    preserved_records = tuple(records)

    # Stage 9 — Dashboard Identity Generation
    dashboard_output_id = build_dashboard_output_id(request)

    # Stage 10 — Dashboard Provenance Generation
    provenance = build_dashboard_provenance(request)

    # Stage 11 — Output Construction
    output = to_dashboard_output(
        dashboard_output_id=dashboard_output_id,
        as_of=request.as_of,
        records=preserved_records,
        provenance=provenance,
    )

    # Stage 12 — Post-Validation
    validated = validate_dashboard_output(output, request=request)

    # Stage 13 — Emission (exactly one complete output)
    return validated
