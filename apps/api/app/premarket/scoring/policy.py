"""Premarket Scoring configuration constants and Decimal policy."""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal

POLICY_VERSION_V1 = "premarket.scoring.policy.v1"
WEIGHT_PROFILE_DEFAULT_V1 = "default_v1"
ORDERING_POLICY_SCORE_DESC_INSTRUMENT_KEY_ASC_ID_ASC = (
    "score_desc_instrument_key_asc_score_record_id_asc"
)
SCORE_QUANTIZE_POLICY_ID = "decimal_8dp_half_even"
IDENTITY_SPECIFICATION_V1 = "premarket.score.identity.v1"

SCORE_QUANTUM = Decimal("0.00000001")
SCORE_ROUNDING = ROUND_HALF_EVEN

FEATURE_WATCHLIST_RANK = "watchlist_rank"
FEATURE_GAP_MAGNITUDE = "gap_magnitude"
FEATURE_CATALYST_PRESENCE = "catalyst_presence"
