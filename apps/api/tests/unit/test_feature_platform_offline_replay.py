"""Unit tests for Feature Platform offline/replay batch materialization."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from app.features.catalog import BAR_CLOSE, BAR_OHLCV_FEATURE_IDS, BAR_OPEN
from app.features.errors import (
    FeaturePlatformDisabledError,
    FeaturePlatformUnsupportedEventError,
)
from app.features.offline_replay import materialize_bar_feature_snapshot_sequence
from app.features.settings import FeaturePlatformSettings
from app.market_data.events.bar import BarEvent
from tests.support.market_data_fixtures import T0, make_bar, make_trade, source


def _bar_at(
    *,
    minutes: int,
    close: Decimal,
    open_: Decimal,
    event_id: str,
) -> BarEvent:
    close_time = T0 + timedelta(minutes=minutes)
    return make_bar(
        occurred_at=close_time,
        effective_at=close_time,
        known_at=close_time + timedelta(milliseconds=50),
        ingested_at=close_time + timedelta(milliseconds=100),
        window_start=close_time - timedelta(minutes=1),
        window_end=close_time,
        close_time=close_time,
        open=open_,
        high=close + Decimal("0.50"),
        low=open_ - Decimal("0.50"),
        close=close,
        volume=Decimal("1000"),
        source=source(source_event_id=event_id),
    )


def test_empty_sequence_returns_empty_tuple() -> None:
    assert materialize_bar_feature_snapshot_sequence(()) == ()
    assert materialize_bar_feature_snapshot_sequence([]) == ()


def test_single_bar_sequence_maps_catalog_values() -> None:
    snapshots = materialize_bar_feature_snapshot_sequence((make_bar(),))
    assert len(snapshots) == 1
    by_id = {feature.feature_id: feature for feature in snapshots[0].features}
    assert by_id[BAR_OPEN].value == Decimal("190.00")
    assert by_id[BAR_CLOSE].value == Decimal("190.20")
    assert set(BAR_OHLCV_FEATURE_IDS).issubset(by_id)


def test_multi_bar_preserves_order_and_decimal_values() -> None:
    first = _bar_at(minutes=0, close=Decimal("100.00"), open_=Decimal("99.00"), event_id="evt-a")
    second = _bar_at(minutes=1, close=Decimal("101.50"), open_=Decimal("101.00"), event_id="evt-b")
    snapshots = materialize_bar_feature_snapshot_sequence((first, second))
    assert len(snapshots) == 2
    closes = [
        next(f.value for f in snap.features if f.feature_id == BAR_CLOSE) for snap in snapshots
    ]
    assert closes == [Decimal("100.00"), Decimal("101.50")]
    assert snapshots[0].snapshot_id != snapshots[1].snapshot_id


def test_identical_ordered_inputs_produce_identical_ordered_fingerprints() -> None:
    bars = (
        _bar_at(minutes=0, close=Decimal("100.00"), open_=Decimal("99.00"), event_id="evt-a"),
        _bar_at(minutes=1, close=Decimal("101.00"), open_=Decimal("100.00"), event_id="evt-b"),
    )
    first = materialize_bar_feature_snapshot_sequence(bars)
    second = materialize_bar_feature_snapshot_sequence(bars)
    assert [snap.fingerprint() for snap in first] == [snap.fingerprint() for snap in second]


def test_input_order_affects_output_order() -> None:
    early = _bar_at(
        minutes=0, close=Decimal("100.00"), open_=Decimal("99.00"), event_id="evt-early"
    )
    late = _bar_at(minutes=5, close=Decimal("110.00"), open_=Decimal("109.00"), event_id="evt-late")
    forward = materialize_bar_feature_snapshot_sequence((early, late))
    reverse = materialize_bar_feature_snapshot_sequence((late, early))
    forward_fps = [snap.fingerprint() for snap in forward]
    reverse_fps = [snap.fingerprint() for snap in reverse]
    assert forward_fps != reverse_fps
    assert forward_fps[0] == reverse_fps[1]
    assert forward_fps[1] == reverse_fps[0]


def test_non_bar_in_sequence_fails_closed_before_any_output() -> None:
    with pytest.raises(FeaturePlatformUnsupportedEventError) as exc_info:
        materialize_bar_feature_snapshot_sequence((make_bar(), make_trade()))
    assert exc_info.value.detail == "unsupported_event:TradeEvent:index=1"


def test_leading_non_bar_fails_closed() -> None:
    with pytest.raises(FeaturePlatformUnsupportedEventError) as exc_info:
        materialize_bar_feature_snapshot_sequence((make_trade(), make_bar()))
    assert exc_info.value.detail == "unsupported_event:TradeEvent:index=0"


def test_sequence_respects_disabled_settings() -> None:
    with pytest.raises(FeaturePlatformDisabledError) as exc_info:
        materialize_bar_feature_snapshot_sequence(
            (make_bar(),),
            settings=FeaturePlatformSettings(enabled=False),
        )
    assert exc_info.value.detail == "feature_platform_disabled"


def test_sequence_runs_when_settings_enabled() -> None:
    snapshots = materialize_bar_feature_snapshot_sequence(
        (make_bar(),),
        settings=FeaturePlatformSettings(enabled=True),
    )
    assert len(snapshots) == 1
