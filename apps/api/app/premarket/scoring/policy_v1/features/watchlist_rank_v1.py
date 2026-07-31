"""Feature Specification ``watchlist_rank.v1``."""

from __future__ import annotations

from decimal import Decimal

from app.premarket.scoring.policy import FEATURE_WATCHLIST_RANK
from app.premarket.scoring.ports import FeatureObservation, InstrumentScoreContext


class WatchlistRankFeatureV1:
    """Map Watchlist rank into a unit component where better rank yields higher value."""

    @property
    def feature_id(self) -> str:
        return FEATURE_WATCHLIST_RANK

    def extract(self, ctx: InstrumentScoreContext) -> FeatureObservation:
        n = len(ctx.watchlist.entries)
        rank = ctx.entry.rank
        raw = (Decimal(n - rank + 1) / Decimal(n)) if n > 0 else Decimal("0")
        return FeatureObservation(
            feature_id=self.feature_id,
            raw_value=raw,
            source_identifiers=(ctx.entry.instrument_key,),
            watchlist_rank=rank,
            watchlist_rule_id=ctx.entry.rule_id,
        )
