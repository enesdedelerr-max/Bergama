"""Policy Version v1 binder."""

from __future__ import annotations

from collections.abc import Sequence

from app.premarket.scoring.policy import POLICY_VERSION_V1, WEIGHT_PROFILE_DEFAULT_V1
from app.premarket.scoring.policy_v1.features.catalyst_presence_v1 import CatalystPresenceFeatureV1
from app.premarket.scoring.policy_v1.features.gap_magnitude_v1 import GapMagnitudeFeatureV1
from app.premarket.scoring.policy_v1.features.watchlist_rank_v1 import WatchlistRankFeatureV1
from app.premarket.scoring.policy_v1.identity_v1 import ScoreIdentityV1Builder
from app.premarket.scoring.policy_v1.params import build_policy_v1_params
from app.premarket.scoring.policy_v1.weight_profile_default_v1 import (
    build_default_v1_weight_profile,
)
from app.premarket.scoring.ports import (
    FeatureExtractor,
    IdentityBuilder,
    PolicyParams,
    WeightProfile,
)


class PolicyVersionV1Binder:
    """Binds Policy Version ``premarket.scoring.policy.v1`` into the pipeline."""

    @property
    def policy_version_id(self) -> str:
        return POLICY_VERSION_V1

    @property
    def weight_profile_id(self) -> str:
        return WEIGHT_PROFILE_DEFAULT_V1

    def resolve_params(self) -> PolicyParams:
        return build_policy_v1_params()

    def weight_profile(self) -> WeightProfile:
        return build_default_v1_weight_profile()

    def feature_extractors(self) -> Sequence[FeatureExtractor]:
        return (
            WatchlistRankFeatureV1(),
            GapMagnitudeFeatureV1(),
            CatalystPresenceFeatureV1(),
        )

    def identity_builder(self) -> IdentityBuilder:
        return ScoreIdentityV1Builder()
