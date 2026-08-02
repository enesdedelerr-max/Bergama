"""Output Builder for Morning Briefing public contracts."""

from __future__ import annotations

from decimal import Decimal

from app.premarket.morning_briefing.models import (
    BriefingCollection,
    BriefingProvenance,
    BriefingRecord,
)
from app.premarket.morning_briefing.policy import (
    ORDERING_PRESERVATION_POLICY_V1,
    POLICY_VERSION_V1,
)
from app.premarket.scoring.models import ScoreRecord


def _canonicalize_preserved_score(score: Decimal) -> Decimal:
    """Preserve score exactly except map signed zero to Decimal('0')."""
    if score.is_zero():
        return Decimal("0")
    return score


def to_briefing_record(*, sequence_index: int, score_record: ScoreRecord) -> BriefingRecord:
    """Map a preserved ScoreRecord into an immutable BriefingRecord."""
    return BriefingRecord(
        sequence_index=sequence_index,
        score_record_id=score_record.score_record_id,
        instrument_key=score_record.instrument_key,
        local_symbol=score_record.local_symbol,
        score=_canonicalize_preserved_score(score_record.score),
        components=score_record.components,
        scoring_policy_version_id=score_record.policy_version_id,
        scoring_weight_profile_id=score_record.weight_profile_id,
        scoring_as_of=score_record.as_of,
        watchlist_rank=score_record.watchlist_rank,
        watchlist_rule_id=score_record.watchlist_rule_id,
        gap_record_id=score_record.gap_record_id,
        catalyst_source_identifiers=score_record.catalyst_source_identifiers,
    )


def to_briefing_collection(
    *,
    briefing_id: str,
    as_of: object,
    records: tuple[BriefingRecord, ...],
    provenance: BriefingProvenance,
) -> BriefingCollection:
    """Materialize an immutable Morning Briefing output."""
    return BriefingCollection(
        briefing_id=briefing_id,
        policy_version_id=POLICY_VERSION_V1,
        ordering_preservation_policy_id=ORDERING_PRESERVATION_POLICY_V1,
        as_of=as_of,  # type: ignore[arg-type]
        records=records,
        provenance=provenance,
    )
