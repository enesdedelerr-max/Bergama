"""FeatureSchemaRegistry helpers for Feature Platform bar catalog (#67)."""

from __future__ import annotations

from app.features.catalog import (
    BAR_FEATURE_SCHEMA_ID,
    BAR_FEATURE_SCHEMA_VERSION,
    bar_feature_catalog,
)
from app.strategy.sdk_runtime.feature_registry import (
    FeatureSchemaDefinition,
    FeatureSchemaRegistry,
)


def build_bar_feature_schema_registry() -> FeatureSchemaRegistry:
    """Register closed bar-field definitions into a host FeatureSchemaRegistry."""
    registry = FeatureSchemaRegistry(closed=True)
    for definition in bar_feature_catalog():
        registry.register(
            FeatureSchemaDefinition(
                schema_id=BAR_FEATURE_SCHEMA_ID,
                schema_version=BAR_FEATURE_SCHEMA_VERSION,
                feature_id=definition.feature_id,
            )
        )
    return registry
