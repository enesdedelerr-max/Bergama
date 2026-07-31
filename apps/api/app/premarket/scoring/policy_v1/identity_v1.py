"""Identity Specification ``premarket.score.identity.v1``."""

from __future__ import annotations

from app.market_data.money import canonical_decimal_str
from app.premarket.scoring.policy import IDENTITY_SPECIFICATION_V1
from app.premarket.scoring.ports import ScoreIdentityInput
from app.strategy.keys import strategy_sha256


class ScoreIdentityV1Builder:
    """Deterministic score identity builder for Policy Version v1."""

    def build_id(self, draft: ScoreIdentityInput) -> str:
        """Return sha256 hex identity over the canonical v1 payload."""
        return strategy_sha256(
            {
                "schema": IDENTITY_SPECIFICATION_V1,
                "policy_version_id": draft.policy_version_id,
                "weight_profile_id": draft.weight_profile_id,
                "instrument_key": draft.instrument_key,
                "as_of": draft.as_of,
                "score": canonical_decimal_str(draft.score),
                "components": {
                    "watchlist_rank": canonical_decimal_str(draft.components.watchlist_rank),
                    "gap_magnitude": (
                        None
                        if draft.components.gap_magnitude is None
                        else canonical_decimal_str(draft.components.gap_magnitude)
                    ),
                    "catalyst_presence": (
                        None
                        if draft.components.catalyst_presence is None
                        else canonical_decimal_str(draft.components.catalyst_presence)
                    ),
                },
                "watchlist_rank": draft.watchlist_rank,
                "watchlist_rule_id": draft.watchlist_rule_id,
                "gap_record_id": draft.gap_record_id or "",
                "catalyst_source_identifiers": list(draft.catalyst_source_identifiers),
            }
        )
