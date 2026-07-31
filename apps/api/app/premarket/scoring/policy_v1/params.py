"""Policy Version v1 parameters."""

from __future__ import annotations

from decimal import Decimal

from app.premarket.scoring.policy import (
    IDENTITY_SPECIFICATION_V1,
    ORDERING_POLICY_SCORE_DESC_INSTRUMENT_KEY_ASC_ID_ASC,
    POLICY_VERSION_V1,
    SCORE_QUANTIZE_POLICY_ID,
    WEIGHT_PROFILE_DEFAULT_V1,
)
from app.premarket.scoring.ports import PolicyParams

GAP_REF_V1 = Decimal("0.10")


def build_policy_v1_params() -> PolicyParams:
    """Return immutable Policy Version v1 parameters."""
    return PolicyParams(
        policy_version_id=POLICY_VERSION_V1,
        weight_profile_id=WEIGHT_PROFILE_DEFAULT_V1,
        ordering_policy_id=ORDERING_POLICY_SCORE_DESC_INSTRUMENT_KEY_ASC_ID_ASC,
        score_quantize_policy_id=SCORE_QUANTIZE_POLICY_ID,
        identity_specification_id=IDENTITY_SPECIFICATION_V1,
        gap_ref=GAP_REF_V1,
    )
