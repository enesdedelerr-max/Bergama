"""Contract tests for Feature Platform → Strategy SDK snapshot compatibility."""

from __future__ import annotations

from app.features.materializer import materialize_bar_feature_snapshot
from bergama_strategy_sdk import FeatureSnapshot, FeatureValue
from tests.support.market_data_fixtures import make_bar


def test_materialized_snapshot_is_sdk_feature_snapshot() -> None:
    snapshot = materialize_bar_feature_snapshot(make_bar())
    assert isinstance(snapshot, FeatureSnapshot)
    assert all(isinstance(feature, FeatureValue) for feature in snapshot.features)
    # Round-trip through SDK model validation without schema edits.
    restored = FeatureSnapshot.model_validate(snapshot.model_dump())
    assert restored.fingerprint() == snapshot.fingerprint()


def test_materialized_snapshot_rejects_duplicate_feature_ids_via_sdk() -> None:
    snapshot = materialize_bar_feature_snapshot(make_bar())
    feature_ids = [feature.feature_id for feature in snapshot.features]
    assert len(feature_ids) == len(set(feature_ids))
