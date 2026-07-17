"""Downstream publish delivery-context and adapter identity tests (#406)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.market_data.enums import AssetClass
from app.market_data.identity import InstrumentId
from app.strategy.errors import StrategyDownstreamPublishError
from app.strategy.models import StrategyDecision as LegacyStrategyDecision
from app.strategy.sdk_runtime.bootstrap import (
    build_reference_feature_registry,
    reference_plugin_manifest,
    reference_runtime_policy,
    reference_strategy_config,
)
from app.strategy.sdk_runtime.engine import build_strategy_sdk_runtime_engine
from app.strategy.sdk_runtime.health import PluginHealth
from app.strategy.sdk_runtime.reference import SdkNoOpStrategy
from app.strategy.sdk_runtime.registry import StrategySdkPluginRegistry
from app.strategy.sdk_runtime.sdk_decision_adapter import sdk_decision_to_legacy
from bergama_strategy_sdk.decisions import StrategyAction, StrategyDecision, StrategyReasonCode
from bergama_strategy_sdk.errors import StrategyContractViolation
from bergama_strategy_sdk.fingerprints import build_decision_id
from bergama_strategy_sdk.manifest import StrategyPluginManifest
from bergama_strategy_sdk.permissions import PluginPermissions
from bergama_strategy_sdk.testing import sample_execution_context, sample_feature_snapshot
from tests.support.strategy_sdk_helpers import (
    execution_context_for_binding,
    sample_instrument_id,
    sdk_runtime_session,
)


class CountingFailPort:
    def __init__(self, *, fail_on: int) -> None:
        self.fail_on = fail_on
        self.calls = 0
        self.published: list[str] = []

    async def publish_decision(self, decision: LegacyStrategyDecision) -> None:
        self.calls += 1
        if self.calls >= self.fail_on:
            raise RuntimeError("downstream boom")
        self.published.append(decision.decision_id)


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
async def test_downstream_failure_on_first_publish_has_empty_published_ids() -> None:
    session, _ = sdk_runtime_session(port=CountingFailPort(fail_on=1))
    snapshot = sample_feature_snapshot()
    contexts = {"noop": execution_context_for_binding(session.bindings[0], snapshot=snapshot)}
    with pytest.raises(StrategyDownstreamPublishError) as exc:
        await session.evaluate_batch(
            feature_snapshot=snapshot,
            instrument_id=sample_instrument_id(),
            contexts=contexts,
        )
    assert exc.value.published_decision_ids == ()
    assert exc.value.failed_decision_id is not None
    assert exc.value.strategy_id == "noop"
    assert session.bindings[0].lifecycle.health is PluginHealth.READY


@pytest.mark.asyncio
async def test_downstream_failure_after_successful_publishes_exposes_ordered_ids() -> None:
    port = CountingFailPort(fail_on=2)
    registry = StrategySdkPluginRegistry()
    first = reference_plugin_manifest()
    second = _second_manifest()
    registry.register(first, lambda _m: SdkNoOpStrategy())
    registry.register(second, lambda _m: SdkNoOpStrategy())
    engine = build_strategy_sdk_runtime_engine(
        registry=registry,
        feature_registry=build_reference_feature_registry(),
        compatibility_policy=reference_runtime_policy(),
        decision_port=port,
    )
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        plugins=(
            (first, reference_strategy_config(), "noop:aapl:1"),
            (second, reference_strategy_config(), "noop2:aapl:1"),
        ),
    )
    snapshot = sample_feature_snapshot()
    contexts = {
        "noop": execution_context_for_binding(session.bindings[0], snapshot=snapshot),
        "noop2": execution_context_for_binding(session.bindings[1], snapshot=snapshot),
    }
    with pytest.raises(StrategyDownstreamPublishError) as exc:
        await session.evaluate_batch(
            feature_snapshot=snapshot,
            instrument_id=sample_instrument_id(),
            contexts=contexts,
        )
    assert len(exc.value.published_decision_ids) == 1
    assert exc.value.published_decision_ids == tuple(port.published)
    assert exc.value.failed_decision_id is not None
    assert exc.value.failed_decision_id not in exc.value.published_decision_ids
    assert exc.value.strategy_id == "noop2"
    assert session.bindings[0].lifecycle.health is PluginHealth.READY
    assert session.bindings[1].lifecycle.health is PluginHealth.READY
    assert "boom" not in str(exc.value)
    assert "stack" not in str(exc.value.__dict__)


@pytest.mark.asyncio
async def test_downstream_failure_after_two_publishes_keeps_deterministic_order() -> None:
    port = CountingFailPort(fail_on=3)
    registry = StrategySdkPluginRegistry()
    manifests = [
        reference_plugin_manifest(),
        _second_manifest(),
        StrategyPluginManifest(
            strategy_id="noop3",
            strategy_version="1.0.0",
            sdk_schema_version="1.0.0",
            runtime_protocol_version="1.0.0",
            feature_schema_version="1.0.0",
            config_schema_version="1.0.0",
            author="bergama",
            package_identity="bergama.reference.noop3",
            required_features=("EMA20", "EMA50"),
            permissions=PluginPermissions.empty(),
            capabilities={"supports_replay": True},
        ),
    ]
    for manifest in manifests:
        registry.register(manifest, lambda _m: SdkNoOpStrategy())
    engine = build_strategy_sdk_runtime_engine(
        registry=registry,
        feature_registry=build_reference_feature_registry(),
        compatibility_policy=reference_runtime_policy(),
        decision_port=port,
    )
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        plugins=tuple(
            (manifest, reference_strategy_config(), f"{manifest.strategy_id}:aapl")
            for manifest in manifests
        ),
    )
    snapshot = sample_feature_snapshot()
    contexts = {
        binding.lifecycle.manifest.strategy_id: execution_context_for_binding(
            binding, snapshot=snapshot
        )
        for binding in session.bindings
    }
    with pytest.raises(StrategyDownstreamPublishError) as exc:
        await session.evaluate_batch(
            feature_snapshot=snapshot,
            instrument_id=sample_instrument_id(),
            contexts=contexts,
        )
    assert exc.value.published_decision_ids == tuple(port.published)
    assert len(exc.value.published_decision_ids) == 2
    assert exc.value.strategy_id == "noop3"


def test_adapter_preserves_real_instrument_identity() -> None:
    snapshot = sample_feature_snapshot()
    context = sample_execution_context(snapshot=snapshot)
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
        snapshot=snapshot,
        action=StrategyAction.NO_ACTION,
        confidence=0.0,
        reason_codes=(StrategyReasonCode.NO_ACTION_REFERENCE,),
        processing_latency_ms=0.0,
        occurred_at=context.evaluation_time,
        decision_timestamp=context.evaluation_time,
    )
    instrument = sample_instrument_id()
    legacy = sdk_decision_to_legacy(decision, instrument_id=instrument, quality_summary=None)
    assert legacy.instrument_id == instrument
    assert legacy.decision_id == decision.decision_id


def test_adapter_rejects_instrument_key_mismatch() -> None:
    snapshot = sample_feature_snapshot()
    context = sample_execution_context(snapshot=snapshot)
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
        snapshot=snapshot,
        action=StrategyAction.NO_ACTION,
        confidence=0.0,
        reason_codes=(StrategyReasonCode.NO_ACTION_REFERENCE,),
        processing_latency_ms=0.0,
        occurred_at=context.evaluation_time,
        decision_timestamp=context.evaluation_time,
    )
    wrong = InstrumentId(
        instrument_key="equity:MSFT:XNYS",
        asset_class=AssetClass.EQUITY,
        local_symbol="MSFT",
        symbol_effective_from=datetime(2020, 1, 1, tzinfo=UTC),
    )
    with pytest.raises(StrategyContractViolation) as exc:
        sdk_decision_to_legacy(decision, instrument_id=wrong, quality_summary=None)
    assert exc.value.detail is not None
    assert "instrument_key_mismatch" in exc.value.detail


@pytest.mark.asyncio
async def test_evaluate_batch_rejects_instrument_snapshot_mismatch() -> None:
    session, _ = sdk_runtime_session()
    snapshot = sample_feature_snapshot()
    contexts = {"noop": sample_execution_context(snapshot=snapshot)}
    wrong = InstrumentId(
        instrument_key="equity:MSFT:XNYS",
        asset_class=AssetClass.EQUITY,
        local_symbol="MSFT",
        symbol_effective_from=datetime(2020, 1, 1, tzinfo=UTC),
    )
    with pytest.raises(StrategyContractViolation) as exc:
        await session.evaluate_batch(
            feature_snapshot=snapshot,
            instrument_id=wrong,
            contexts=contexts,
        )
    assert exc.value.detail == "instrument_key_mismatch"
