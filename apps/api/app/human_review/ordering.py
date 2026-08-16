"""Ordering Preservation for Human Review Policy Version v1."""

from __future__ import annotations

from app.dashboard.models import DashboardPresentationOutput, DashboardPresentationRecord
from app.human_review.errors import HumanReviewOrderingError
from app.human_review.models import HumanReviewUpstreamReferenceRecord


def preserve_dashboard_order(
    dashboard: DashboardPresentationOutput,
) -> tuple[tuple[int, DashboardPresentationRecord], ...]:
    """Preserve Dashboard order exactly; no independent ranking."""
    return tuple((index, record) for index, record in enumerate(dashboard.records))


def assert_ordering_preserved(
    *,
    dashboard: DashboardPresentationOutput,
    records: tuple[HumanReviewUpstreamReferenceRecord, ...],
) -> None:
    """Fail closed when Human Review order diverges from Dashboard order."""
    if len(records) != len(dashboard.records):
        raise HumanReviewOrderingError(detail="ordering_length_mismatch")
    for index, (review_record, dashboard_record) in enumerate(
        zip(records, dashboard.records, strict=True)
    ):
        if review_record.sequence_index != index:
            raise HumanReviewOrderingError(
                detail=f"sequence_index_mismatch:{index}:{review_record.sequence_index}"
            )
        if review_record.score_record_id != dashboard_record.score_record_id:
            raise HumanReviewOrderingError(detail=f"ordering_score_record_id_mismatch:{index}")
        if review_record.instrument_key != dashboard_record.instrument_key:
            raise HumanReviewOrderingError(detail=f"ordering_instrument_key_mismatch:{index}")
        if review_record.score != dashboard_record.score and not (
            review_record.score.is_zero() and dashboard_record.score.is_zero()
        ):
            raise HumanReviewOrderingError(detail=f"ordering_score_mutation:{index}")
