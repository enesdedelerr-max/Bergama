"""Host feature resolution for Strategy SDK (#67).

Chooses Feature Platform bar materialization when enabled; otherwise preserves
explicit FeatureAssembler / legacy feature-value assembly.
"""

from __future__ import annotations

from decimal import Decimal

from bergama_strategy_sdk.features import FeatureSnapshot

from app.core.feature_platform_settings import FeaturePlatformSettings
from app.features.errors import FeaturePlatformUnsupportedEventError
from app.features.materializer import materialize_bar_feature_snapshot
from app.market_data.events.bar import BarEvent
from app.strategy.models import StrategyInput
from app.strategy.sdk_runtime.feature_assembler import FeatureAssembler
from app.strategy.sdk_runtime.legacy_adapter import strategy_input_to_feature_snapshot
from app.strategy.sdk_runtime.metrics import StrategySdkRuntimeMetrics


def resolve_feature_snapshot_for_strategy_input(
    strategy_input: StrategyInput,
    *,
    feature_platform: FeaturePlatformSettings,
    assembler: FeatureAssembler,
    required_features: tuple[str, ...],
    feature_values: dict[str, Decimal] | None = None,
    metrics: StrategySdkRuntimeMetrics | None = None,
) -> FeatureSnapshot:
    """Resolve a FeatureSnapshot for strategy evaluation.

    - Feature Platform disabled: existing assembler path (explicit feature values).
    - Feature Platform enabled: require BarEvent and materialize via Feature Platform.
    """
    if feature_platform.enabled:
        event = strategy_input.event
        if not isinstance(event, BarEvent):
            event_type = type(event).__name__
            raise FeaturePlatformUnsupportedEventError(detail=f"unsupported_event:{event_type}")
        return materialize_bar_feature_snapshot(event, settings=feature_platform)

    return strategy_input_to_feature_snapshot(
        strategy_input,
        assembler=assembler,
        required_features=required_features,
        feature_values=feature_values,
        metrics=metrics,
    )
