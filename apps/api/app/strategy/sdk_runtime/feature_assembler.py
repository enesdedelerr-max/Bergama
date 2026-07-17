"""Host feature assembly into immutable FeatureSnapshot (#406)."""

from __future__ import annotations

from decimal import Decimal

from bergama_strategy_sdk.errors import StrategyFeatureSchemaError
from bergama_strategy_sdk.features import FeatureSnapshot, FeatureValue

from app.strategy.sdk_runtime.feature_registry import FeatureSchemaRegistry


class FeatureAssembler:
    """Assembles host-provided feature values into FeatureSnapshot."""

    def __init__(self, *, registry: FeatureSchemaRegistry, feature_schema_version: str) -> None:
        self._registry = registry
        self._feature_schema_version = feature_schema_version

    def assemble(
        self,
        *,
        instrument_key: str,
        snapshot_id: str,
        required_features: tuple[str, ...],
        values: dict[str, Decimal],
    ) -> FeatureSnapshot:
        self._registry.validate_required_features(required_features)
        features: list[FeatureValue] = []
        for feature_id in sorted(required_features):
            if feature_id not in values:
                raise StrategyFeatureSchemaError(detail=f"missing_feature_value:{feature_id}")
            schema = self._registry.find_by_feature_id(feature_id)
            features.append(
                FeatureValue(
                    feature_id=feature_id,
                    schema_id=schema.schema_id,
                    schema_version=schema.schema_version,
                    value=values[feature_id],
                )
            )
        return FeatureSnapshot(
            feature_schema_version=self._feature_schema_version,
            instrument_key=instrument_key,
            snapshot_id=snapshot_id,
            features=tuple(features),
        )
