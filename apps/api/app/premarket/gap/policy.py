"""Gap Scanner configuration constants and Decimal policy."""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal

SELECTION_POLICY_TWO_BARS_BY_CLOSE_TIME_V1 = "two_bars_by_close_time_v1"
GAP_PERCENT_QUANTIZE_POLICY_ID = "decimal_8dp_half_even"
GAP_PERCENT_QUANTUM = Decimal("0.00000001")
GAP_PERCENT_ROUNDING = ROUND_HALF_EVEN

GAP_DIRECTION_UP = "up"
GAP_DIRECTION_DOWN = "down"
GAP_DIRECTION_FLAT = "flat"
