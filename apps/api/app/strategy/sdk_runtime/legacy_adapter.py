"""Versioned legacy StrategyInput compatibility adapter (#406)."""

from __future__ import annotations

from decimal import Decimal

from bergama_strategy_sdk.errors import StrategyCompatibilityError, StrategyFeatureSchemaError
from bergama_strategy_sdk.features import FeatureSnapshot

from app.core.strategy_sdk_settings import StrategySdkRuntimeSettings
from app.market_data.identity import InstrumentId
from app.strategy.models import StrategyInput
from app.strategy.sdk_runtime.feature_assembler import FeatureAssembler
from app.strategy.sdk_runtime.metrics import StrategySdkRuntimeMetrics

ADAPTER_VERSION = "1.0.0"


def strategy_input_to_feature_snapshot(
    strategy_input: StrategyInput,
    *,
    assembler: FeatureAssembler,
    required_features: tuple[str, ...],
    feature_values: dict[str, Decimal] | None = None,
    metrics: StrategySdkRuntimeMetrics | None = None,
) -> FeatureSnapshot:
    """Explicit deterministic adapter — no hidden provider/network access."""
    if not required_features:
        raise StrategyFeatureSchemaError(detail="adapter_requires_declared_features")
    values = feature_values if feature_values is not None else {}
    if not values:
        raise StrategyFeatureSchemaError(detail="adapter_missing_feature_values")
    try:
        return assembler.assemble(
            instrument_key=strategy_input.instrument_id.instrument_key,
            snapshot_id=strategy_input.idempotency_key,
            required_features=required_features,
            values=values,
        )
    except StrategyFeatureSchemaError:
        if metrics is not None:
            metrics.feature_assembly_error_total += 1
        raise


def convert_legacy_strategy_input(
    strategy_input: StrategyInput,
    *,
    settings: StrategySdkRuntimeSettings,
    assembler: FeatureAssembler,
    required_features: tuple[str, ...],
    feature_values: dict[str, Decimal],
    host_instrument_id: InstrumentId,
    metrics: StrategySdkRuntimeMetrics | None = None,
) -> FeatureSnapshot:
    """Gated #406 compatibility path. Disabled unless explicitly enabled."""
    if not settings.legacy_adapter_enabled:
        raise StrategyCompatibilityError(detail="legacy_adapter_disabled")
    if host_instrument_id != strategy_input.instrument_id:
        raise StrategyFeatureSchemaError(detail="adapter_instrument_identity_mismatch")
    if not host_instrument_id.instrument_key.strip():
        raise StrategyFeatureSchemaError(detail="adapter_missing_instrument_identity")
    return strategy_input_to_feature_snapshot(
        strategy_input,
        assembler=assembler,
        required_features=required_features,
        feature_values=feature_values,
        metrics=metrics,
    )


def adapter_version() -> str:
    return ADAPTER_VERSION
