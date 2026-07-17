"""Deterministic SDK test harness utilities."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from bergama_strategy_sdk.config import StrategyConfig
from bergama_strategy_sdk.context import StrategyExecutionContext
from bergama_strategy_sdk.features import FeatureSnapshot, FeatureValue
from bergama_strategy_sdk.fingerprints import (
    configuration_fingerprint,
    execution_fingerprint,
    feature_fingerprint,
    strategy_fingerprint,
)
from bergama_strategy_sdk.state import PreviousStrategyState


def fixed_evaluation_time() -> datetime:
    return datetime(2026, 7, 15, 14, 30, tzinfo=UTC)


def sample_feature_snapshot() -> FeatureSnapshot:
    return FeatureSnapshot(
        feature_schema_version="1.0.0",
        instrument_key="equity:AAPL:XNYS",
        snapshot_id="snap-1",
        features=(
            FeatureValue(
                feature_id="EMA20",
                schema_id="technical",
                schema_version="1.0.0",
                value=Decimal("150.25"),
            ),
            FeatureValue(
                feature_id="EMA50",
                schema_id="technical",
                schema_version="1.0.0",
                value=Decimal("148.10"),
            ),
        ),
    )


def sample_config() -> StrategyConfig:
    return StrategyConfig(config_schema_version="1.0.0", safe_metadata={"purpose": "test"})


def sample_previous_state() -> PreviousStrategyState:
    return PreviousStrategyState(
        state_schema_version="1.0.0",
        state_id="state-1",
        payload={"step": "0"},
    )


def sample_execution_context(
    *,
    snapshot: FeatureSnapshot | None = None,
    config: StrategyConfig | None = None,
    previous_state: PreviousStrategyState | None = None,
) -> StrategyExecutionContext:
    resolved_snapshot = snapshot if snapshot is not None else sample_feature_snapshot()
    resolved_config = config if config is not None else sample_config()
    feature_fp = feature_fingerprint(resolved_snapshot.fingerprint_payload())
    config_fp = configuration_fingerprint(resolved_config.fingerprint_payload())
    strategy_fp = strategy_fingerprint(
        strategy_id="noop",
        strategy_version="1.0.0",
        strategy_instance_id="noop:aapl:primary",
        sdk_schema_version="1.0.0",
    )
    previous_fp = previous_state.fingerprint() if previous_state is not None else None
    execution_fp = execution_fingerprint(
        strategy_fingerprint_value=strategy_fp,
        feature_fingerprint_value=feature_fp,
        configuration_fingerprint_value=config_fp,
        runtime_protocol_version="1.0.0",
        previous_state_fingerprint=previous_fp,
    )
    return StrategyExecutionContext(
        execution_id="exec-1",
        strategy_id="noop",
        strategy_version="1.0.0",
        strategy_instance_id="noop:aapl:primary",
        run_id="run-1",
        session_id="session-1",
        evaluation_time=fixed_evaluation_time(),
        sdk_schema_version="1.0.0",
        runtime_protocol_version="1.0.0",
        feature_schema_version="1.0.0",
        config_schema_version="1.0.0",
        strategy_fingerprint=strategy_fp,
        feature_fingerprint=feature_fp,
        configuration_fingerprint=config_fp,
        execution_fingerprint=execution_fp,
    )
