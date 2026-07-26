"""Closed Feature Platform catalog for BarEvent field projection."""

from __future__ import annotations

from dataclasses import dataclass

FEATURE_PLATFORM_SCHEMA_VERSION = "1.0.0"
BAR_FEATURE_SCHEMA_ID = "bar"
BAR_FEATURE_SCHEMA_VERSION = "1.0.0"

BAR_OPEN = "bar.open"
BAR_HIGH = "bar.high"
BAR_LOW = "bar.low"
BAR_CLOSE = "bar.close"
BAR_VOLUME = "bar.volume"
BAR_VWAP = "bar.vwap"

BAR_OHLCV_FEATURE_IDS: tuple[str, ...] = (
    BAR_OPEN,
    BAR_HIGH,
    BAR_LOW,
    BAR_CLOSE,
    BAR_VOLUME,
)


@dataclass(frozen=True, slots=True)
class BarFeatureDefinition:
    feature_id: str
    schema_id: str = BAR_FEATURE_SCHEMA_ID
    schema_version: str = BAR_FEATURE_SCHEMA_VERSION
    required: bool = True


def bar_feature_catalog() -> tuple[BarFeatureDefinition, ...]:
    """Return the closed bar-field catalog for this vertical slice."""
    required = tuple(
        BarFeatureDefinition(feature_id=feature_id, required=True)
        for feature_id in BAR_OHLCV_FEATURE_IDS
    )
    optional_vwap = BarFeatureDefinition(feature_id=BAR_VWAP, required=False)
    return (*required, optional_vwap)
