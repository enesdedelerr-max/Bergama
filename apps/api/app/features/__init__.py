"""Feature Platform bounded context — Sprint 6 foundation."""

from __future__ import annotations

from app.features.catalog import (
    BAR_FEATURE_SCHEMA_ID,
    BAR_FEATURE_SCHEMA_VERSION,
    BAR_OHLCV_FEATURE_IDS,
    FEATURE_PLATFORM_SCHEMA_VERSION,
    BarFeatureDefinition,
    bar_feature_catalog,
)
from app.features.errors import (
    FeaturePlatformDisabledError,
    FeaturePlatformError,
    FeaturePlatformUnsupportedEventError,
    FeaturePlatformValidationError,
)
from app.features.materializer import materialize_bar_feature_snapshot
from app.features.settings import FeaturePlatformSettings

__all__ = [
    "BAR_FEATURE_SCHEMA_ID",
    "BAR_FEATURE_SCHEMA_VERSION",
    "BAR_OHLCV_FEATURE_IDS",
    "FEATURE_PLATFORM_SCHEMA_VERSION",
    "BarFeatureDefinition",
    "FeaturePlatformDisabledError",
    "FeaturePlatformError",
    "FeaturePlatformSettings",
    "FeaturePlatformUnsupportedEventError",
    "FeaturePlatformValidationError",
    "bar_feature_catalog",
    "materialize_bar_feature_snapshot",
]
