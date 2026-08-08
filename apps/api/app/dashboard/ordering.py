"""Ordering Preservation for Dashboard Policy Version v1."""

from __future__ import annotations

from app.dashboard.errors import DashboardOrderingError
from app.dashboard.models import DashboardPresentationRecord
from app.premarket.morning_briefing import BriefingCollection, BriefingRecord


def preserve_morning_briefing_order(
    briefing: BriefingCollection,
) -> tuple[tuple[int, BriefingRecord], ...]:
    """Preserve Morning Briefing order exactly; no independent ranking."""
    return tuple((index, record) for index, record in enumerate(briefing.records))


def assert_ordering_preserved(
    *,
    briefing: BriefingCollection,
    records: tuple[DashboardPresentationRecord, ...],
) -> None:
    """Fail closed when Dashboard order diverges from Morning Briefing order."""
    if len(records) != len(briefing.records):
        raise DashboardOrderingError(detail="ordering_length_mismatch")
    for index, (dashboard_record, briefing_record) in enumerate(
        zip(records, briefing.records, strict=True)
    ):
        if dashboard_record.sequence_index != index:
            raise DashboardOrderingError(
                detail=f"sequence_index_mismatch:{index}:{dashboard_record.sequence_index}"
            )
        if dashboard_record.score_record_id != briefing_record.score_record_id:
            raise DashboardOrderingError(detail=f"ordering_score_record_id_mismatch:{index}")
        if dashboard_record.instrument_key != briefing_record.instrument_key:
            raise DashboardOrderingError(detail=f"ordering_instrument_key_mismatch:{index}")
        if dashboard_record.score != briefing_record.score and not (
            dashboard_record.score.is_zero() and briefing_record.score.is_zero()
        ):
            raise DashboardOrderingError(detail=f"ordering_score_mutation:{index}")
