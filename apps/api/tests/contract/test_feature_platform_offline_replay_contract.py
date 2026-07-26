"""Contract tests for offline/replay Feature Platform batch materialization."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from app.features.catalog import BAR_OHLCV_FEATURE_IDS, BAR_VWAP, bar_feature_catalog
from app.features.offline_replay import materialize_bar_feature_snapshot_sequence
from bergama_strategy_sdk import FeatureSnapshot, FeatureValue
from tests.support.market_data_fixtures import T0, make_bar, source


def _two_bars() -> tuple[object, object]:
    second_close = T0 + timedelta(minutes=1)
    first = make_bar(source=source(source_event_id="contract-evt-1"))
    second = make_bar(
        occurred_at=second_close,
        effective_at=second_close,
        known_at=second_close + timedelta(milliseconds=50),
        ingested_at=second_close + timedelta(milliseconds=100),
        window_start=second_close - timedelta(minutes=1),
        window_end=second_close,
        close_time=second_close,
        open=Decimal("191.00"),
        high=Decimal("191.50"),
        low=Decimal("190.80"),
        close=Decimal("191.20"),
        volume=Decimal("11000"),
        vwap=Decimal("191.10"),
        source=source(source_event_id="contract-evt-2"),
    )
    return first, second


def test_empty_sequence_contract() -> None:
    assert materialize_bar_feature_snapshot_sequence(()) == ()


def test_sequence_snapshots_are_frozen_sdk_models() -> None:
    snapshots = materialize_bar_feature_snapshot_sequence(_two_bars())
    assert len(snapshots) == 2
    for snapshot in snapshots:
        assert isinstance(snapshot, FeatureSnapshot)
        assert all(isinstance(feature, FeatureValue) for feature in snapshot.features)
        restored = FeatureSnapshot.model_validate(snapshot.model_dump())
        assert restored.fingerprint() == snapshot.fingerprint()
        assert all(isinstance(feature.value, Decimal) for feature in snapshot.features)


def test_sequence_uses_only_closed_bar_catalog_ids() -> None:
    allowed = {item.feature_id for item in bar_feature_catalog()}
    assert allowed == set(BAR_OHLCV_FEATURE_IDS) | {BAR_VWAP}
    snapshots = materialize_bar_feature_snapshot_sequence(_two_bars())
    for snapshot in snapshots:
        ids = {feature.feature_id for feature in snapshot.features}
        assert ids.issubset(allowed)
        assert set(BAR_OHLCV_FEATURE_IDS).issubset(ids)


def test_ordered_sequence_fingerprints_are_deterministic() -> None:
    bars = _two_bars()
    first = materialize_bar_feature_snapshot_sequence(bars)
    second = materialize_bar_feature_snapshot_sequence(bars)
    assert [snap.fingerprint() for snap in first] == [snap.fingerprint() for snap in second]
