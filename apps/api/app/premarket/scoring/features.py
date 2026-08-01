"""Feature Extraction Layer for Premarket Scoring."""

from __future__ import annotations

from app.premarket.errors import ScoreDuplicateInstrumentError
from app.premarket.scoring.ports import (
    AbsentFeature,
    BoundPolicyContext,
    FeatureObservation,
    InstrumentScoreContext,
    ValidatedScoreRequest,
)


def extract_features(
    request: ValidatedScoreRequest,
    bound: BoundPolicyContext,
) -> dict[str, tuple[FeatureObservation | AbsentFeature, ...]]:
    """Extract Policy Version feature observations for every Watchlist instrument.

    Iteration order follows Watchlist entry order. Final collection order is
    deferred to the Ordering Engine.
    """
    seen: set[str] = set()
    by_instrument: dict[str, tuple[FeatureObservation | AbsentFeature, ...]] = {}

    for entry in request.watchlist.entries:
        instrument_key = entry.instrument_key
        if instrument_key in seen:
            raise ScoreDuplicateInstrumentError(detail=f"duplicate_instrument:{instrument_key}")
        seen.add(instrument_key)

        ctx = InstrumentScoreContext(
            entry=entry,
            watchlist=request.watchlist,
            as_of=request.as_of,
            catalysts=request.catalysts,
            gaps=request.gaps,
            params=bound.params,
        )
        observations: list[FeatureObservation | AbsentFeature] = []
        for extractor in bound.feature_extractors:
            observations.append(extractor.extract(ctx))
        by_instrument[instrument_key] = tuple(observations)

    return by_instrument
