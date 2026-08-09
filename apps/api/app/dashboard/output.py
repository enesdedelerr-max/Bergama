"""Output builder for Dashboard public contracts."""

from __future__ import annotations

from decimal import Decimal

from app.dashboard.models import (
    DashboardPresentationOutput,
    DashboardPresentationRecord,
    DashboardProvenance,
)
from app.dashboard.policy import (
    ORDERING_PRESERVATION_POLICY_V1,
    POLICY_VERSION_V1,
    PRESENTATION_SELECTION_POLICY_V1,
    REQUIRED_UPSTREAM_BRIEFING_POLICY_VERSION_ID,
)
from app.premarket.morning_briefing import BriefingRecord


def _canonicalize_preserved_score(score: Decimal) -> Decimal:
    """Preserve score exactly except map signed zero to Decimal('0')."""
    if score.is_zero():
        return Decimal("0")
    return score


def to_dashboard_record(
    *,
    sequence_index: int,
    briefing_record: BriefingRecord,
    morning_briefing_policy_version_id: str = REQUIRED_UPSTREAM_BRIEFING_POLICY_VERSION_ID,
) -> DashboardPresentationRecord:
    """Map a preserved Morning Briefing record into a Dashboard presentation record."""
    return DashboardPresentationRecord(
        sequence_index=sequence_index,
        score_record_id=briefing_record.score_record_id,
        instrument_key=briefing_record.instrument_key,
        local_symbol=briefing_record.local_symbol,
        score=_canonicalize_preserved_score(briefing_record.score),
        components=briefing_record.components,
        morning_briefing_policy_version_id=morning_briefing_policy_version_id,
        scoring_policy_version_id=briefing_record.scoring_policy_version_id,
        scoring_weight_profile_id=briefing_record.scoring_weight_profile_id,
        scoring_as_of=briefing_record.scoring_as_of,
        watchlist_rank=briefing_record.watchlist_rank,
        watchlist_rule_id=briefing_record.watchlist_rule_id,
        gap_record_id=briefing_record.gap_record_id,
        catalyst_source_identifiers=briefing_record.catalyst_source_identifiers,
    )


def to_dashboard_output(
    *,
    dashboard_output_id: str,
    as_of: object,
    records: tuple[DashboardPresentationRecord, ...],
    provenance: DashboardProvenance,
) -> DashboardPresentationOutput:
    """Materialize an immutable Dashboard presentation output."""
    return DashboardPresentationOutput(
        dashboard_output_id=dashboard_output_id,
        policy_version_id=POLICY_VERSION_V1,
        ordering_preservation_policy_id=ORDERING_PRESERVATION_POLICY_V1,
        presentation_selection_policy_id=PRESENTATION_SELECTION_POLICY_V1,
        as_of=as_of,  # type: ignore[arg-type]
        records=records,
        provenance=provenance,
    )
