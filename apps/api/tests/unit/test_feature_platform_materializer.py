"""Unit tests for Feature Platform BarEvent materialization."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.features.catalog import (
    BAR_CLOSE,
    BAR_OHLCV_FEATURE_IDS,
    BAR_OPEN,
    BAR_VWAP,
    bar_feature_catalog,
)
from app.features.errors import (
    FeaturePlatformDisabledError,
    FeaturePlatformUnsupportedEventError,
)
from app.features.materializer import materialize_bar_feature_snapshot
from app.features.settings import FeaturePlatformSettings
from tests.support.market_data_fixtures import make_bar, make_trade


def test_bar_feature_catalog_is_closed_and_ordered() -> None:
    catalog = bar_feature_catalog()
    ids = tuple(item.feature_id for item in catalog)
    assert ids[:5] == BAR_OHLCV_FEATURE_IDS
    assert ids[-1] == BAR_VWAP
    assert all(item.required for item in catalog[:-1])
    assert catalog[-1].required is False


def test_materialize_bar_maps_ohlcv_and_optional_vwap() -> None:
    bar = make_bar()
    snapshot = materialize_bar_feature_snapshot(bar)
    by_id = {feature.feature_id: feature for feature in snapshot.features}
    assert by_id[BAR_OPEN].value == Decimal("190.00")
    assert by_id[BAR_CLOSE].value == Decimal("190.20")
    assert by_id[BAR_VWAP].value == Decimal("190.10")
    assert snapshot.instrument_key == bar.instrument.instrument_key
    assert snapshot.feature_schema_version == "1.0.0"
    assert all(feature.value == feature.value.normalize() for feature in snapshot.features)


def test_materialize_bar_omits_vwap_when_absent() -> None:
    bar = make_bar(vwap=None)
    snapshot = materialize_bar_feature_snapshot(bar)
    ids = {feature.feature_id for feature in snapshot.features}
    assert BAR_VWAP not in ids
    assert set(BAR_OHLCV_FEATURE_IDS) == ids


def test_materialize_bar_fingerprint_is_deterministic() -> None:
    bar = make_bar()
    first = materialize_bar_feature_snapshot(bar)
    second = materialize_bar_feature_snapshot(bar)
    assert first.fingerprint() == second.fingerprint()
    assert first.model_dump() == second.model_dump()


def test_materialize_rejects_non_bar_events() -> None:
    trade = make_trade()
    with pytest.raises(FeaturePlatformUnsupportedEventError, match="unsupported_event"):
        materialize_bar_feature_snapshot(trade)


def test_materialize_fails_closed_when_disabled() -> None:
    bar = make_bar()
    settings = FeaturePlatformSettings(enabled=False)
    with pytest.raises(FeaturePlatformDisabledError) as exc_info:
        materialize_bar_feature_snapshot(bar, settings=settings)
    assert exc_info.value.detail == "feature_platform_disabled"


def test_materialize_runs_when_enabled() -> None:
    bar = make_bar()
    settings = FeaturePlatformSettings(enabled=True)
    snapshot = materialize_bar_feature_snapshot(bar, settings=settings)
    assert snapshot.features
