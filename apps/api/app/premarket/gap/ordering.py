"""Deterministic gap collection ordering policy."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.premarket.gap.models import GapRecord

ORDERING_POLICY_ABS_GAP_DESC_INSTRUMENT_KEY_ASC_ID_ASC = "abs_gap_desc_instrument_key_asc_id_asc"


def gap_sort_key(record: GapRecord) -> tuple[object, ...]:
    """Stable total order: abs(gap) DESC, instrument_key ASC, gap_record_id ASC."""
    return (
        -abs(record.gap_percent),
        record.instrument_key,
        record.gap_record_id,
    )
