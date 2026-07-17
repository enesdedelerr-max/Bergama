"""Strategy SDK runtime session tests (#406)."""

from __future__ import annotations

import asyncio

import pytest
from app.strategy.errors import StrategyDownstreamPublishError
from app.strategy.models import StrategyDecision as LegacyStrategyDecision
from app.strategy.ports import InMemoryStrategyDecisionPort
from app.strategy.sdk_runtime.bootstrap import (
    build_reference_feature_registry,
    reference_plugin_manifest,
    reference_runtime_policy,
    reference_strategy_config,
)
from app.strategy.sdk_runtime.engine import build_strategy_sdk_runtime_engine
from app.strategy.sdk_runtime.health import PluginHealth
from app.strategy.sdk_runtime.registry import StrategySdkPluginRegistry
from bergama_strategy_sdk.config import StrategyConfig
from bergama_strategy_sdk.context import StrategyExecutionContext
from bergama_strategy_sdk.decisions import StrategyAction, StrategyDecision, StrategyReasonCode
from bergama_strategy_sdk.execution import StrategyExecutionOutput
from bergama_strategy_sdk.features import FeatureSnapshot
from bergama_strategy_sdk.fingerprints import build_decision_id
from bergama_strategy_sdk.manifest import StrategyPluginManifest
from bergama_strategy_sdk.permissions import PluginPermissions
from bergama_strategy_sdk.state import PreviousStrategyState
from tests.support.strategy_sdk_helpers import (
    execution_context_for_binding,
    sample_batch_context,
    sample_instrument_id,
    sdk_runtime_session,
)


@pytest.mark.asyncio
async def test_reference_plugin_emits_deterministic_batch_result() -> None:
    session, port = sdk_runtime_session()
    snapshot, contexts = sample_batch_context()
    result = await session.evaluate_batch(
        feature_snapshot=snapshot,
        instrument_id=sample_instrument_id(),
        contexts=contexts,
    )
    assert len(result.decisions) == 1
    assert result.execution_summary.succeeded == 1
    assert result.execution_summary.failed == 0
    assert len(port.decisions) == 1
    assert port.decisions[0].instrument_id == sample_instrument_id()


@pytest.mark.asyncio
async def test_plugin_crash_disables_only_failed_plugin_and_continues() -> None:
    registry = StrategySdkPluginRegistry()
    manifest = reference_plugin_manifest()
    registry.register(manifest, lambda _m: CrashingStrategy())
    registry.register(second_manifest(), lambda _m: WorkingStrategy())
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
            (manifest, reference_strategy_config(), "noop:aapl:primary"),
            (second_manifest(), reference_strategy_config(), "noop2:aapl:primary"),
        ),
    )
    snapshot, _ = sample_batch_context()
    contexts = {
        "noop": execution_context_for_binding(session.bindings[0], snapshot=snapshot),
        "noop2": execution_context_for_binding(session.bindings[1], snapshot=snapshot),
    }
    result = await session.evaluate_batch(
        feature_snapshot=snapshot,
        instrument_id=sample_instrument_id(),
        contexts=contexts,
    )
    assert result.execution_summary.succeeded == 1
    assert result.execution_summary.failed == 1
    assert result.plugin_failures[0].strategy_id == "noop"
    assert result.plugin_failures[0].plugin_health is PluginHealth.DISABLED
    assert "stack" not in result.plugin_failures[0].safe_metadata


@pytest.mark.asyncio
async def test_cancelled_error_propagates_without_disabling_plugin() -> None:
    registry = StrategySdkPluginRegistry()
    manifest = reference_plugin_manifest()
    registry.register(manifest, lambda _m: CancellingStrategy())
    engine = build_strategy_sdk_runtime_engine(
        registry=registry,
        feature_registry=build_reference_feature_registry(),
        compatibility_policy=reference_runtime_policy(),
        decision_port=InMemoryStrategyDecisionPort(),
    )
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        plugins=((manifest, reference_strategy_config(), "noop:aapl:primary"),),
    )
    snapshot, contexts = sample_batch_context()
    with pytest.raises(asyncio.CancelledError):
        await session.evaluate_batch(
            feature_snapshot=snapshot,
            instrument_id=sample_instrument_id(),
            contexts=contexts,
        )
    assert session.bindings[0].lifecycle.health is PluginHealth.READY


@pytest.mark.asyncio
async def test_downstream_failure_does_not_disable_plugin() -> None:
    session, _ = sdk_runtime_session(port=FailingDecisionPort())
    snapshot, contexts = sample_batch_context()
    with pytest.raises(StrategyDownstreamPublishError) as exc:
        await session.evaluate_batch(
            feature_snapshot=snapshot,
            instrument_id=sample_instrument_id(),
            contexts=contexts,
        )
    assert session.bindings[0].lifecycle.health is PluginHealth.READY
    assert exc.value.published_decision_ids == ()
    assert exc.value.failed_decision_id is not None
    assert exc.value.strategy_id == "noop"
    assert "RuntimeError" in (exc.value.detail or "")


def second_manifest() -> StrategyPluginManifest:
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


class CrashingStrategy:
    async def execute(
        self,
        *,
        previous_state: PreviousStrategyState | None,
        feature_snapshot: FeatureSnapshot,
        context: StrategyExecutionContext,
        config: StrategyConfig,
    ) -> StrategyExecutionOutput:
        _ = previous_state, feature_snapshot, context, config
        raise RuntimeError("boom")


class WorkingStrategy:
    async def execute(
        self,
        *,
        previous_state: PreviousStrategyState | None,
        feature_snapshot: FeatureSnapshot,
        context: StrategyExecutionContext,
        config: StrategyConfig,
    ) -> StrategyExecutionOutput:
        action = StrategyAction.NO_ACTION
        decision_id = build_decision_id(
            strategy_id=context.strategy_id,
            strategy_version=context.strategy_version,
            strategy_instance_id=context.strategy_instance_id,
            run_id=context.run_id,
            execution_fingerprint_value=context.execution_fingerprint,
            action=action.value,
            runtime_protocol_version=context.runtime_protocol_version,
        )
        decision = StrategyDecision.from_execution(
            decision_id=decision_id,
            context=context,
            snapshot=feature_snapshot,
            action=action,
            confidence=0.0,
            reason_codes=(StrategyReasonCode.NO_ACTION_REFERENCE,),
            processing_latency_ms=0.0,
            occurred_at=context.evaluation_time,
            decision_timestamp=context.evaluation_time,
        )
        return StrategyExecutionOutput(decision=decision, next_state=None)


class CancellingStrategy:
    async def execute(
        self,
        *,
        previous_state: PreviousStrategyState | None,
        feature_snapshot: FeatureSnapshot,
        context: StrategyExecutionContext,
        config: StrategyConfig,
    ) -> StrategyExecutionOutput:
        _ = previous_state, feature_snapshot, context, config
        raise asyncio.CancelledError


class FailingDecisionPort:
    async def publish_decision(self, decision: LegacyStrategyDecision) -> None:
        _ = decision
        raise RuntimeError("sink boom")
