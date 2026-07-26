"""Deterministic BarEvent → FeatureSnapshot materializer."""

from __future__ import annotations

from datetime import UTC
from decimal import Decimal

from bergama_strategy_sdk import FeatureSnapshot, FeatureValue

from app.features.catalog import (
    BAR_CLOSE,
    BAR_FEATURE_SCHEMA_ID,
    BAR_FEATURE_SCHEMA_VERSION,
    BAR_HIGH,
    BAR_LOW,
    BAR_OPEN,
    BAR_VOLUME,
    BAR_VWAP,
    FEATURE_PLATFORM_SCHEMA_VERSION,
)
from app.features.errors import (
    FeaturePlatformDisabledError,
    FeaturePlatformError,
    FeaturePlatformUnsupportedEventError,
    FeaturePlatformValidationError,
)
from app.features.settings import FeaturePlatformSettings
from app.market_data.events.bar import BarEvent


def _feature_value(*, feature_id: str, value: Decimal, unit: str | None) -> FeatureValue:
    return FeatureValue(
        feature_id=feature_id,
        schema_id=BAR_FEATURE_SCHEMA_ID,
        schema_version=BAR_FEATURE_SCHEMA_VERSION,
        value=value,
        unit=unit,
    )


def _snapshot_id(bar: BarEvent) -> str:
    close_time = bar.close_time.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return f"bar:{bar.instrument.instrument_key}:{close_time}:{bar.source.source_event_id}"


def materialize_bar_feature_snapshot(
    event: object,
    *,
    settings: FeaturePlatformSettings | None = None,
) -> FeatureSnapshot:
    """Project a canonical BarEvent into a Sprint 5-compatible FeatureSnapshot.

    When ``settings`` is provided, enablement must be true (fail-closed).
    When ``settings`` is omitted, materialization runs for direct unit use.
    """
    if settings is not None and not settings.enabled:
        raise FeaturePlatformDisabledError(detail="feature_platform_disabled")

    if not isinstance(event, BarEvent):
        event_type = type(event).__name__
        raise FeaturePlatformUnsupportedEventError(detail=f"unsupported_event:{event_type}")

    try:
        instrument_key = event.instrument.instrument_key.strip()
        if not instrument_key:
            raise FeaturePlatformValidationError(detail="missing_instrument_key")

        price_unit = event.currency
        features: list[FeatureValue] = [
            _feature_value(feature_id=BAR_OPEN, value=event.open, unit=price_unit),
            _feature_value(feature_id=BAR_HIGH, value=event.high, unit=price_unit),
            _feature_value(feature_id=BAR_LOW, value=event.low, unit=price_unit),
            _feature_value(feature_id=BAR_CLOSE, value=event.close, unit=price_unit),
            _feature_value(feature_id=BAR_VOLUME, value=event.volume, unit=None),
        ]
        if event.vwap is not None:
            features.append(_feature_value(feature_id=BAR_VWAP, value=event.vwap, unit=price_unit))

        schema_version = (
            settings.feature_schema_version
            if settings is not None
            else FEATURE_PLATFORM_SCHEMA_VERSION
        )
        return FeatureSnapshot(
            feature_schema_version=schema_version,
            instrument_key=instrument_key,
            snapshot_id=_snapshot_id(event),
            features=tuple(features),
        )
    except FeaturePlatformError:
        raise
    except Exception as exc:
        raise FeaturePlatformValidationError(detail=f"invalid_bar:{exc}") from exc
