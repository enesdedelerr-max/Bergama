"""Output Builder for Premarket Scoring public contracts."""

from __future__ import annotations

from app.premarket.scoring.models import ScoreCollection, ScoreProvenance, ScoreRecord
from app.premarket.scoring.ports import ScoreRecordDraft


def to_score_record(draft: ScoreRecordDraft) -> ScoreRecord:
    """Map an internal draft to an immutable public ScoreRecord."""
    return ScoreRecord(
        score_record_id=draft.score_record_id,
        instrument_key=draft.instrument_key,
        local_symbol=draft.local_symbol,
        score=draft.score,
        components=draft.components,
        policy_version_id=draft.policy_version_id,
        weight_profile_id=draft.weight_profile_id,
        as_of=draft.as_of,
        watchlist_rank=draft.watchlist_rank,
        watchlist_rule_id=draft.watchlist_rule_id,
        gap_record_id=draft.gap_record_id,
        catalyst_source_identifiers=draft.catalyst_source_identifiers,
    )


def to_score_collection(
    *,
    as_of: object,
    drafts: tuple[ScoreRecordDraft, ...],
    provenance: ScoreProvenance,
) -> ScoreCollection:
    """Materialize an immutable ScoreCollection."""
    records = tuple(to_score_record(draft) for draft in drafts)
    return ScoreCollection(
        as_of=as_of,  # type: ignore[arg-type]
        records=records,
        provenance=provenance,
    )
