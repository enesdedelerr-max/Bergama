"""State ownership, budgets, and recovery tests (#406)."""

from __future__ import annotations

import asyncio

import pytest
from app.strategy.ports import InMemoryStrategyDecisionPort
from app.strategy.sdk_runtime.bootstrap import (
    build_reference_feature_registry,
    reference_plugin_manifest,
    reference_runtime_policy,
    reference_strategy_config,
)
from app.strategy.sdk_runtime.budgets import ExecutionBudgets
from app.strategy.sdk_runtime.engine import build_strategy_sdk_runtime_engine
from app.strategy.sdk_runtime.health import PluginHealth
from app.strategy.sdk_runtime.reference import SdkNoOpStrategy
from app.strategy.sdk_runtime.registry import StrategySdkPluginRegistry
from bergama_strategy_sdk.config import StrategyConfig
from bergama_strategy_sdk.context import StrategyExecutionContext
from bergama_strategy_sdk.decisions import StrategyAction, StrategyDecision, StrategyReasonCode
from bergama_strategy_sdk.errors import StrategyBudgetExceededError, StrategyStateError
from bergama_strategy_sdk.execution import StrategyExecutionOutput
from bergama_strategy_sdk.features import FeatureSnapshot
from bergama_strategy_sdk.fingerprints import build_decision_id
from bergama_strategy_sdk.manifest import StrategyPluginManifest
from bergama_strategy_sdk.permissions import PluginPermissions
from bergama_strategy_sdk.state import NextStrategyState, PreviousStrategyState
from bergama_strategy_sdk.testing import sample_feature_snapshot
from tests.support.strategy_sdk_helpers import (
    execution_context_for_binding,
    sample_instrument_id,
    sdk_runtime_session,
)


def _second_manifest() -> StrategyPluginManifest:
    return StrategyPluginManifest(
        strategy_id="noop2",
        strategy_version="1.0.0",
        sdk_schema_version="1.0.0",
        runtime_protocol_version="1.0.0",
        feature_schema_version="1.0.0",
        config_schema_version="1.0.0",
        author="bergama",
        package_identity="bergama.reference.noop2",
        required_features=("EMA20", "EMA50"),
        permissions=PluginPermissions.empty(),
        capabilities={"supports_replay": True},
    )


@pytest.mark.asyncio
async def test_compatible_previous_state_and_next_state_are_preserved() -> None:
    session, _ = sdk_runtime_session()
    snapshot = sample_feature_snapshot()
    previous = PreviousStrategyState(
        state_schema_version="1.0.0",
        state_id="state-1",
        strategy_id="noop",
        strategy_instance_id="noop:aapl:primary",
        payload={"step": "3"},
    )
    result = await session.evaluate_batch(
        feature_snapshot=snapshot,
        instrument_id=sample_instrument_id(),
        contexts={"noop": execution_context_for_binding(session.bindings[0], snapshot=snapshot)},
        previous_states={"noop": previous},
    )
    assert len(result.state_commits) == 1
    assert result.state_commits[0].next_state.payload["step"] == "4"
    assert result.state_commits[0].next_state.fingerprint()


@pytest.mark.asyncio
async def test_state_schema_mismatch_disables_plugin_and_continues() -> None:
    registry = StrategySdkPluginRegistry()
    first = reference_plugin_manifest()
    second = _second_manifest()
    registry.register(first, lambda _m: SdkNoOpStrategy())
    registry.register(second, lambda _m: SdkNoOpStrategy())
    engine = build_strategy_sdk_runtime_engine(
        registry=registry,
        feature_registry=build_reference_feature_registry(),
        compatibility_policy=reference_runtime_policy(),
        decision_port=InMemoryStrategyDecisionPort(),
    )
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        plugins=(
            (first, reference_strategy_config(), "noop:aapl:primary"),
            (second, reference_strategy_config(), "noop2:aapl:primary"),
        ),
    )
    snapshot = sample_feature_snapshot()
    contexts = {
        "noop": execution_context_for_binding(session.bindings[0], snapshot=snapshot),
        "noop2": execution_context_for_binding(session.bindings[1], snapshot=snapshot),
    }
    result = await session.evaluate_batch(
        feature_snapshot=snapshot,
        instrument_id=sample_instrument_id(),
        contexts=contexts,
        previous_states={
            "noop": PreviousStrategyState(
                state_schema_version="9.9.9",
                state_id="state-1",
                payload={"step": "0"},
            )
        },
    )
    assert result.execution_summary.failed == 1
    assert result.execution_summary.succeeded == 1
    assert result.plugin_failures[0].failure_type == "StrategyStateError"
    assert session.bindings[0].lifecycle.health is PluginHealth.DISABLED
    assert session.bindings[1].lifecycle.health is PluginHealth.READY
    assert session.metrics.snapshot()["state_error_total"] == 1


def test_oversized_previous_state_rejected_by_budget() -> None:
    budgets = ExecutionBudgets(max_state_bytes=32)
    state = PreviousStrategyState(
        state_schema_version="1.0.0",
        state_id="state-1",
        payload={"step": "x" * 200},
    )
    with pytest.raises(StrategyBudgetExceededError) as exc:
        budgets.validate_state(state)
    assert exc.value.detail == "state"


def test_oversized_next_state_rejected_by_budget() -> None:
    budgets = ExecutionBudgets(max_state_bytes=32)
    state = NextStrategyState(
        state_schema_version="1.0.0",
        state_id="state-1",
        payload={"step": "x" * 200},
    )
    with pytest.raises(StrategyBudgetExceededError) as exc:
        budgets.validate_state(state)
    assert exc.value.detail == "state"


def test_budget_boundaries_for_safe_metadata_and_manifest() -> None:
    budgets = ExecutionBudgets(max_safe_metadata_bytes=40, max_manifest_bytes=10_000)
    budgets.validate_safe_metadata({"a": "1"})
    with pytest.raises(StrategyBudgetExceededError):
        budgets.validate_safe_metadata({"note": "x" * 200})
    manifest = reference_plugin_manifest()
    budgets.validate_manifest(manifest)
    tiny = ExecutionBudgets(max_manifest_bytes=8)
    with pytest.raises(StrategyBudgetExceededError):
        tiny.validate_manifest(manifest)


@pytest.mark.asyncio
async def test_output_budget_violation_disables_plugin() -> None:
    class FatStrategy:
        async def execute(
            self,
            *,
            previous_state: PreviousStrategyState | None,
            feature_snapshot: FeatureSnapshot,
            context: StrategyExecutionContext,
            config: StrategyConfig,
        ) -> StrategyExecutionOutput:
            _ = previous_state, config
            decision_id = build_decision_id(
                strategy_id=context.strategy_id,
                strategy_version=context.strategy_version,
                strategy_instance_id=context.strategy_instance_id,
                run_id=context.run_id,
                execution_fingerprint_value=context.execution_fingerprint,
                action=StrategyAction.NO_ACTION.value,
                runtime_protocol_version=context.runtime_protocol_version,
            )
            decision = StrategyDecision.from_execution(
                decision_id=decision_id,
                context=context,
                snapshot=feature_snapshot,
                action=StrategyAction.NO_ACTION,
                confidence=0.0,
                reason_codes=(StrategyReasonCode.NO_ACTION_REFERENCE,),
                processing_latency_ms=0.0,
                occurred_at=context.evaluation_time,
                decision_timestamp=context.evaluation_time,
                safe_metadata={"blob": "y" * 200},
            )
            return StrategyExecutionOutput(decision=decision, next_state=None)

    registry = StrategySdkPluginRegistry()
    manifest = reference_plugin_manifest()
    registry.register(manifest, lambda _m: FatStrategy())
    engine = build_strategy_sdk_runtime_engine(
        registry=registry,
        feature_registry=build_reference_feature_registry(),
        compatibility_policy=reference_runtime_policy(),
        decision_port=InMemoryStrategyDecisionPort(),
        budgets=ExecutionBudgets(max_safe_metadata_bytes=32, max_output_bytes=10_000),
    )
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        plugins=((manifest, reference_strategy_config(), "noop:aapl:primary"),),
    )
    snapshot = sample_feature_snapshot()
    result = await session.evaluate_batch(
        feature_snapshot=snapshot,
        instrument_id=sample_instrument_id(),
        contexts={"noop": execution_context_for_binding(session.bindings[0], snapshot=snapshot)},
    )
    assert result.execution_summary.failed == 1
    assert result.plugin_failures[0].failure_type == "StrategyBudgetExceededError"
    assert session.bindings[0].lifecycle.health is PluginHealth.DISABLED
    assert "y" * 50 not in str(result.plugin_failures[0])


@pytest.mark.asyncio
async def test_timeout_releases_lock_and_disables_plugin() -> None:
    class SlowStrategy:
        async def execute(
            self,
            *,
            previous_state: PreviousStrategyState | None,
            feature_snapshot: FeatureSnapshot,
            context: StrategyExecutionContext,
            config: StrategyConfig,
        ) -> StrategyExecutionOutput:
            _ = previous_state, feature_snapshot, context, config
            await asyncio.sleep(1)
            raise AssertionError("should have timed out")

    registry = StrategySdkPluginRegistry()
    manifest = reference_plugin_manifest()
    registry.register(manifest, lambda _m: SlowStrategy())
    engine = build_strategy_sdk_runtime_engine(
        registry=registry,
        feature_registry=build_reference_feature_registry(),
        compatibility_policy=reference_runtime_policy(),
        decision_port=InMemoryStrategyDecisionPort(),
        budgets=ExecutionBudgets(execution_timeout_ms=20),
    )
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        plugins=((manifest, reference_strategy_config(), "noop:aapl:primary"),),
    )
    snapshot = sample_feature_snapshot()
    result = await session.evaluate_batch(
        feature_snapshot=snapshot,
        instrument_id=sample_instrument_id(),
        contexts={"noop": execution_context_for_binding(session.bindings[0], snapshot=snapshot)},
    )
    assert result.plugin_failures[0].failure_type == "StrategyTimeoutError"
    assert session.bindings[0].lifecycle.health is PluginHealth.DISABLED
    assert session.bindings[0].leases == 0
    assert not session.bindings[0].lock.locked()


def test_state_identity_mismatch_raises_typed_error() -> None:
    from app.strategy.sdk_runtime.state_contract import validate_previous_state

    with pytest.raises(StrategyStateError) as exc:
        validate_previous_state(
            PreviousStrategyState(
                state_schema_version="1.0.0",
                state_id="state-1",
                strategy_id="other",
                payload={},
            ),
            strategy_id="noop",
            strategy_instance_id="noop:aapl:primary",
        )
    assert exc.value.detail == "state_strategy_id_mismatch"
