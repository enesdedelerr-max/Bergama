"""Gap Scanner Foundation public exports."""

from __future__ import annotations

from app.premarket.gap.engine import scan_gaps, scan_gaps_from_parts
from app.premarket.gap.identity import build_gap_record_id
from app.premarket.gap.models import (
    GapCollection,
    GapConfig,
    GapProvenance,
    GapRecord,
    GapScanRequest,
)
from app.premarket.gap.normalize import coerce_bar_events
from app.premarket.gap.ordering import (
    ORDERING_POLICY_ABS_GAP_DESC_INSTRUMENT_KEY_ASC_ID_ASC,
    gap_sort_key,
)
from app.premarket.gap.policy import (
    GAP_DIRECTION_DOWN,
    GAP_DIRECTION_FLAT,
    GAP_DIRECTION_UP,
    GAP_PERCENT_QUANTIZE_POLICY_ID,
    SELECTION_POLICY_TWO_BARS_BY_CLOSE_TIME_V1,
)

__all__ = [
    "GAP_DIRECTION_DOWN",
    "GAP_DIRECTION_FLAT",
    "GAP_DIRECTION_UP",
    "GAP_PERCENT_QUANTIZE_POLICY_ID",
    "ORDERING_POLICY_ABS_GAP_DESC_INSTRUMENT_KEY_ASC_ID_ASC",
    "SELECTION_POLICY_TWO_BARS_BY_CLOSE_TIME_V1",
    "GapCollection",
    "GapConfig",
    "GapProvenance",
    "GapRecord",
    "GapScanRequest",
    "build_gap_record_id",
    "coerce_bar_events",
    "gap_sort_key",
    "scan_gaps",
    "scan_gaps_from_parts",
]
