"""Feature Specification ``gap_magnitude.v1``."""

from __future__ import annotations

from decimal import Decimal

from app.premarket.errors import ScoreConflictError, ScoreStaleKnownAtError
from app.premarket.gap.models import GapRecord
from app.premarket.scoring.policy import FEATURE_GAP_MAGNITUDE
from app.premarket.scoring.ports import (
    AbsentFeature,
    FeatureObservation,
    InstrumentScoreContext,
)


class GapMagnitudeFeatureV1:
    """Map absolute overnight gap magnitude into a unit component."""

    @property
    def feature_id(self) -> str:
        return FEATURE_GAP_MAGNITUDE

    def extract(self, ctx: InstrumentScoreContext) -> FeatureObservation | AbsentFeature:
        if ctx.gaps is None:
            return AbsentFeature(feature_id=self.feature_id)

        usable: list[GapRecord] = []
        for record in ctx.gaps.records:
            if record.instrument_key != ctx.entry.instrument_key:
                continue
            if record.known_at > ctx.as_of:
                raise ScoreStaleKnownAtError(
                    detail=f"gap_known_at_after_as_of:{record.gap_record_id}"
                )
            usable.append(record)

        if len(usable) == 0:
            return AbsentFeature(feature_id=self.feature_id)
        if len(usable) > 1:
            raise ScoreConflictError(
                detail=f"duplicate_or_conflicting_gaps:{ctx.entry.instrument_key}:{len(usable)}"
            )

        record = usable[0]
        absolute = abs(record.gap_percent)
        raw = absolute / ctx.params.gap_ref
        if raw > Decimal("1"):
            raw = Decimal("1")
        return FeatureObservation(
            feature_id=self.feature_id,
            raw_value=raw,
            source_identifiers=(record.gap_record_id,),
            gap_record_id=record.gap_record_id,
        )
