"""Offline/replay batch materialization of ordered BarEvents (#Sprint 6).

Converts an ordered BarEvent sequence into FeatureSnapshots in the same order.
Does not persist, network, or access Iceberg/Kafka/databases.
"""

from __future__ import annotations

from collections.abc import Sequence

from bergama_strategy_sdk import FeatureSnapshot

from app.features.errors import FeaturePlatformUnsupportedEventError
from app.features.materializer import materialize_bar_feature_snapshot
from app.features.settings import FeaturePlatformSettings
from app.market_data.events.bar import BarEvent


def materialize_bar_feature_snapshot_sequence(
    events: Sequence[object],
    *,
    settings: FeaturePlatformSettings | None = None,
) -> tuple[FeatureSnapshot, ...]:
    """Materialize an ordered BarEvent sequence into FeatureSnapshots.

    Behavior:
    - Empty sequence → empty tuple (no work, no failure).
    - Each element must be a ``BarEvent``; otherwise fail closed before emitting
      any snapshots (partial failure prevention).
    - Successful outputs preserve input order.
    - Reuses ``materialize_bar_feature_snapshot`` for each bar.
    - When ``settings`` is provided, enablement must be true (same as single-bar).
    """
    if not events:
        return ()

    for index, event in enumerate(events):
        if not isinstance(event, BarEvent):
            event_type = type(event).__name__
            raise FeaturePlatformUnsupportedEventError(
                detail=f"unsupported_event:{event_type}:index={index}"
            )

    return tuple(materialize_bar_feature_snapshot(event, settings=settings) for event in events)
