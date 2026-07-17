"""Shared Strategy SDK runtime test helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.market_data.enums import AssetClass
from app.market_data.identity import InstrumentId
from app.strategy.ports import InMemoryStrategyDecisionPort
from app.strategy.sdk_runtime.bootstrap import (
    build_reference_feature_registry,
    build_reference_plugin_registry,
    reference_plugin_manifest,
    reference_runtime_policy,
    reference_strategy_config,
)
from app.strategy.sdk_runtime.budgets import ExecutionBudgets
from app.strategy.sdk_runtime.engine import build_strategy_sdk_runtime_engine
from app.strategy.sdk_runtime.session import SdkRuntimeBinding
from bergama_strategy_sdk.config import StrategyConfig
from bergama_strategy_sdk.context import StrategyExecutionContext
from bergama_strategy_sdk.features import FeatureSnapshot
from bergama_strategy_sdk.fingerprints import (
    configuration_fingerprint,
    execution_fingerprint,
    feature_fingerprint,
    strategy_fingerprint,
)
from bergama_strategy_sdk.state import PreviousStrategyState
from bergama_strategy_sdk.testing import (
    fixed_evaluation_time,
    sample_execution_context,
    sample_feature_snapshot,
)


def sample_instrument_id() -> InstrumentId:
    """Real host-owned identity matching sample_feature_snapshot().instrument_key."""
    return InstrumentId(
        instrument_key="equity:AAPL:XNYS",
        asset_class=AssetClass.EQUITY,
        local_symbol="AAPL",
        symbol_effective_from=datetime(2020, 1, 1, tzinfo=UTC),
    )


def sdk_runtime_engine(
    *,
    port: InMemoryStrategyDecisionPort | None = None,
) -> tuple:
    resolved_port = port if port is not None else InMemoryStrategyDecisionPort()
    engine = build_strategy_sdk_runtime_engine(
        registry=build_reference_plugin_registry(),
        feature_registry=build_reference_feature_registry(),
        compatibility_policy=reference_runtime_policy(),
        decision_port=resolved_port,
        budgets=ExecutionBudgets(execution_timeout_ms=5_000),
    )
    return engine, resolved_port


def sdk_runtime_session(*, port: InMemoryStrategyDecisionPort | None = None):
    engine, resolved_port = sdk_runtime_engine(port=port)
    manifest = reference_plugin_manifest()
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        plugins=(
            (
                manifest,
                reference_strategy_config(),
                "noop:aapl:primary",
            ),
        ),
    )
    return session, resolved_port


def sample_feature_values() -> dict[str, Decimal]:
    return {
        "EMA20": Decimal("150.25"),
        "EMA50": Decimal("148.10"),
    }


def sample_batch_context():
    snapshot = sample_feature_snapshot()
    return snapshot, {"noop": sample_execution_context(snapshot=snapshot)}


def execution_context_for_binding(
    binding: SdkRuntimeBinding,
    *,
    snapshot: FeatureSnapshot,
    previous_state: PreviousStrategyState | None = None,
    run_id: str = "run-1",
    session_id: str = "session-1",
    execution_id: str = "exec-1",
    config: StrategyConfig | None = None,
) -> StrategyExecutionContext:
    """Build an execution context that matches a leased binding identity."""
    resolved_config = config if config is not None else binding.config
    identity = binding.identity()
    feature_fp = feature_fingerprint(snapshot.fingerprint_payload())
    config_fp = configuration_fingerprint(resolved_config.fingerprint_payload())
    previous_fp = previous_state.fingerprint() if previous_state is not None else None
    strategy_fp = strategy_fingerprint(
        strategy_id=identity.strategy_id,
        strategy_version=identity.strategy_version,
        strategy_instance_id=identity.strategy_instance_id,
        sdk_schema_version=identity.sdk_schema_version,
    )
    execution_fp = execution_fingerprint(
        strategy_fingerprint_value=strategy_fp,
        feature_fingerprint_value=feature_fp,
        configuration_fingerprint_value=config_fp,
        runtime_protocol_version=identity.runtime_protocol_version,
        previous_state_fingerprint=previous_fp,
    )
    return StrategyExecutionContext(
        execution_id=execution_id,
        strategy_id=identity.strategy_id,
        strategy_version=identity.strategy_version,
        strategy_instance_id=identity.strategy_instance_id,
        run_id=run_id,
        session_id=session_id,
        evaluation_time=fixed_evaluation_time(),
        sdk_schema_version=identity.sdk_schema_version,
        runtime_protocol_version=identity.runtime_protocol_version,
        feature_schema_version=identity.feature_schema_version,
        config_schema_version=identity.config_schema_version,
        strategy_fingerprint=strategy_fp,
        feature_fingerprint=feature_fp,
        configuration_fingerprint=config_fp,
        execution_fingerprint=execution_fp,
    )
