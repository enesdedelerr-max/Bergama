"""Weight Engine for Premarket Scoring."""

from __future__ import annotations

from decimal import Decimal

from app.premarket.errors import ScoreValidationError
from app.premarket.scoring.ports import (
    AbsentFeature,
    NormalizedComponent,
    WeightedTerm,
    WeightedTerms,
    WeightProfile,
)
from app.premarket.watchlist.models import WatchlistEntry


def apply_weights(
    *,
    entry: WatchlistEntry,
    components: tuple[NormalizedComponent | AbsentFeature, ...],
    profile: WeightProfile,
) -> WeightedTerms:
    """Apply an immutable Weight Profile without redistributing absent weights."""
    present: dict[str, NormalizedComponent] = {}
    for item in components:
        if isinstance(item, AbsentFeature):
            continue
        if item.feature_id in present:
            raise ScoreValidationError(detail=f"duplicate_feature:{item.feature_id}")
        present[item.feature_id] = item

    terms: list[WeightedTerm] = []
    for feature_id, weight in profile.weights.items():
        component = present.get(feature_id)
        if component is None:
            terms.append(
                WeightedTerm(
                    feature_id=feature_id,
                    value=Decimal("0"),
                    weight=weight,
                    contribution=Decimal("0"),
                    present=False,
                )
            )
            continue
        contribution = weight * component.value
        terms.append(
            WeightedTerm(
                feature_id=feature_id,
                value=component.value,
                weight=weight,
                contribution=contribution,
                present=True,
                source_identifiers=component.source_identifiers,
                gap_record_id=component.gap_record_id,
                watchlist_rank=component.watchlist_rank,
                watchlist_rule_id=component.watchlist_rule_id,
            )
        )

    unknown = set(present) - set(profile.weights)
    if unknown:
        raise ScoreValidationError(detail=f"unknown_features:{sorted(unknown)}")

    return WeightedTerms(
        instrument_key=entry.instrument_key,
        local_symbol=entry.local_symbol,
        terms=tuple(terms),
    )
