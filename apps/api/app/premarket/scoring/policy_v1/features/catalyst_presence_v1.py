"""Feature Specification ``catalyst_presence.v1``."""

from __future__ import annotations

from decimal import Decimal

from app.premarket.errors import ScoreConflictError, ScoreStaleKnownAtError
from app.premarket.scoring.canonical import canonical_source_identifiers
from app.premarket.scoring.policy import FEATURE_CATALYST_PRESENCE
from app.premarket.scoring.ports import (
    AbsentFeature,
    FeatureObservation,
    InstrumentScoreContext,
)


class CatalystPresenceFeatureV1:
    """Map usable catalyst evidence into a binary presence component."""

    @property
    def feature_id(self) -> str:
        return FEATURE_CATALYST_PRESENCE

    def extract(self, ctx: InstrumentScoreContext) -> FeatureObservation | AbsentFeature:
        if ctx.catalysts is None:
            return AbsentFeature(feature_id=self.feature_id)

        by_id: dict[str, object] = {}
        for record in ctx.catalysts.records:
            if record.instrument_key != ctx.entry.instrument_key:
                continue
            if record.known_at > ctx.as_of:
                raise ScoreStaleKnownAtError(
                    detail=f"catalyst_known_at_after_as_of:{record.catalyst_record_id}"
                )
            dumped = record.model_dump(mode="python")
            existing = by_id.get(record.catalyst_record_id)
            if existing is not None and existing != dumped:
                raise ScoreConflictError(
                    detail=f"conflicting_catalyst_identity:{record.catalyst_record_id}"
                )
            by_id[record.catalyst_record_id] = dumped

        matching_ids = canonical_source_identifiers(by_id)
        presence = Decimal("1") if matching_ids else Decimal("0")
        return FeatureObservation(
            feature_id=self.feature_id,
            raw_value=presence,
            source_identifiers=matching_ids,
        )
