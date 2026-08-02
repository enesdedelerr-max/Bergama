"""Ordering Preservation for Morning Briefing Policy Version v1."""

from __future__ import annotations

from app.premarket.errors import BriefingInvariantError
from app.premarket.morning_briefing.models import BriefingRecord
from app.premarket.scoring.models import ScoreCollection, ScoreRecord


def preserve_scoring_order(
    scores: ScoreCollection,
) -> tuple[tuple[int, ScoreRecord], ...]:
    """Preserve Premarket Scoring order exactly; no independent ranking."""
    return tuple((index, record) for index, record in enumerate(scores.records))


def assert_ordering_preserved(
    *,
    scores: ScoreCollection,
    records: tuple[BriefingRecord, ...],
) -> None:
    """Fail closed when briefing order diverges from Premarket Scoring order."""
    if len(records) != len(scores.records):
        raise BriefingInvariantError(detail="ordering_length_mismatch")
    for index, (briefing_record, score_record) in enumerate(
        zip(records, scores.records, strict=True)
    ):
        if briefing_record.sequence_index != index:
            raise BriefingInvariantError(
                detail=f"sequence_index_mismatch:{index}:{briefing_record.sequence_index}"
            )
        if briefing_record.score_record_id != score_record.score_record_id:
            raise BriefingInvariantError(detail=f"ordering_score_record_id_mismatch:{index}")
        if briefing_record.instrument_key != score_record.instrument_key:
            raise BriefingInvariantError(detail=f"ordering_instrument_key_mismatch:{index}")
        if briefing_record.score != score_record.score:
            raise BriefingInvariantError(detail=f"ordering_score_mutation:{index}")
