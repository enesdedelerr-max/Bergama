"""Weight Profile ``default_v1`` for Policy Version v1."""

from __future__ import annotations

from decimal import Decimal
from types import MappingProxyType

from app.premarket.scoring.policy import (
    FEATURE_CATALYST_PRESENCE,
    FEATURE_GAP_MAGNITUDE,
    FEATURE_WATCHLIST_RANK,
    WEIGHT_PROFILE_DEFAULT_V1,
)
from app.premarket.scoring.ports import WeightProfile


def build_default_v1_weight_profile() -> WeightProfile:
    """Return immutable Weight Profile default_v1."""
    return WeightProfile(
        weight_profile_id=WEIGHT_PROFILE_DEFAULT_V1,
        weights=MappingProxyType(
            {
                FEATURE_WATCHLIST_RANK: Decimal("0.50"),
                FEATURE_GAP_MAGNITUDE: Decimal("0.30"),
                FEATURE_CATALYST_PRESENCE: Decimal("0.20"),
            }
        ),
    )
