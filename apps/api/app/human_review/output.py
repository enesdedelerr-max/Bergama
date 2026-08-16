"""Output builder for Human Review public contracts."""

from __future__ import annotations

from decimal import Decimal

from app.dashboard.models import DashboardPresentationRecord
from app.human_review.models import (
    HumanReviewHistoryBinding,
    HumanReviewOutput,
    HumanReviewProvenance,
    HumanReviewRecordedAttestation,
    HumanReviewUpstreamReferenceRecord,
)
from app.human_review.policy import (
    HISTORY_SPECIFICATION_V1,
    HUMAN_ATTESTATION_POLICY_V1,
    IDENTITY_SPECIFICATION_V1,
    ORDERING_PRESERVATION_POLICY_V1,
    POLICY_VERSION_V1,
    PRESENTATION_PRESERVATION_POLICY_V1,
    PROVENANCE_SPECIFICATION_V1,
    REQUIRED_UPSTREAM_DASHBOARD_POLICY_VERSION_ID,
)


def _canonicalize_preserved_score(score: Decimal) -> Decimal:
    """Preserve score exactly except map signed zero to Decimal('0')."""
    if score.is_zero():
        return Decimal("0")
    return score


def to_upstream_record(
    *,
    sequence_index: int,
    dashboard_record: DashboardPresentationRecord,
    dashboard_policy_version_id: str = REQUIRED_UPSTREAM_DASHBOARD_POLICY_VERSION_ID,
) -> HumanReviewUpstreamReferenceRecord:
    """Map a preserved Dashboard record into a Human Review upstream-reference record."""
    return HumanReviewUpstreamReferenceRecord(
        sequence_index=sequence_index,
        score_record_id=dashboard_record.score_record_id,
        instrument_key=dashboard_record.instrument_key,
        local_symbol=dashboard_record.local_symbol,
        score=_canonicalize_preserved_score(dashboard_record.score),
        components=dashboard_record.components,
        dashboard_policy_version_id=dashboard_policy_version_id,
        scoring_as_of=dashboard_record.scoring_as_of,
    )


def to_human_review_output(
    *,
    human_review_output_id: str,
    as_of: object,
    dashboard_output_id: str,
    records: tuple[HumanReviewUpstreamReferenceRecord, ...],
    attestation: HumanReviewRecordedAttestation,
    provenance: HumanReviewProvenance,
    history: HumanReviewHistoryBinding,
) -> HumanReviewOutput:
    """Materialize an immutable Human Review output."""
    return HumanReviewOutput(
        human_review_output_id=human_review_output_id,
        policy_version_id=POLICY_VERSION_V1,
        ordering_preservation_policy_id=ORDERING_PRESERVATION_POLICY_V1,
        presentation_preservation_policy_id=PRESENTATION_PRESERVATION_POLICY_V1,
        human_attestation_policy_id=HUMAN_ATTESTATION_POLICY_V1,
        identity_specification_id=IDENTITY_SPECIFICATION_V1,
        provenance_specification_id=PROVENANCE_SPECIFICATION_V1,
        history_specification_id=HISTORY_SPECIFICATION_V1,
        as_of=as_of,  # type: ignore[arg-type]
        dashboard_output_id=dashboard_output_id,
        records=records,
        attestation=attestation,
        provenance=provenance,
        history=history,
    )
