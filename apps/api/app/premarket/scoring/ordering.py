"""Ordering Engine for Premarket Scoring."""

from __future__ import annotations

from app.premarket.errors import ScoreUnsupportedPolicyError
from app.premarket.scoring.policy import ORDERING_POLICY_SCORE_DESC_INSTRUMENT_KEY_ASC_ID_ASC
from app.premarket.scoring.ports import ScoreRecordDraft


def score_sort_key(draft: ScoreRecordDraft) -> tuple[object, ...]:
    """Stable total order: score DESC, instrument_key ASC, score_record_id ASC."""
    return (
        -draft.score,
        draft.instrument_key,
        draft.score_record_id,
    )


def order_score_drafts(
    drafts: list[ScoreRecordDraft],
    *,
    ordering_policy_id: str,
) -> tuple[ScoreRecordDraft, ...]:
    """Order score drafts under the frozen ordering policy."""
    if ordering_policy_id != ORDERING_POLICY_SCORE_DESC_INSTRUMENT_KEY_ASC_ID_ASC:
        raise ScoreUnsupportedPolicyError(
            detail=f"unsupported_ordering_policy:{ordering_policy_id}"
        )
    return tuple(sorted(drafts, key=score_sort_key))
