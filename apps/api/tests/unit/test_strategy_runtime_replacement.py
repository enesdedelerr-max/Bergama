"""Plugin reload/replacement orchestration tests (#406)."""

from __future__ import annotations

import asyncio
import inspect

import pytest
from app.strategy.ports import InMemoryStrategyDecisionPort
from app.strategy.sdk_runtime.bootstrap import (
    build_reference_feature_registry,
    reference_plugin_manifest,
    reference_runtime_policy,
    reference_strategy_config,
)
from app.strategy.sdk_runtime.engine import build_strategy_sdk_runtime_engine
from app.strategy.sdk_runtime.health import PluginHealth
from app.strategy.sdk_runtime.lifecycle import PluginLifecycle
from app.strategy.sdk_runtime.reference import SdkNoOpStrategy
from app.strategy.sdk_runtime.registry import StrategySdkPluginRegistry
from app.strategy.sdk_runtime.session import StrategySdkRuntimeSession
from bergama_strategy_sdk.compatibility import RuntimeCompatibilityPolicy
from bergama_strategy_sdk.config import StrategyConfig
from bergama_strategy_sdk.context import StrategyExecutionContext
from bergama_strategy_sdk.decisions import StrategyAction, StrategyDecision, StrategyReasonCode
from bergama_strategy_sdk.errors import (
    StrategyCompatibilityError,
    StrategyContractViolation,
    StrategyFeatureSchemaError,
    StrategyManifestError,
)
from bergama_strategy_sdk.execution import StrategyExecutionOutput
from bergama_strategy_sdk.features import FeatureSnapshot
from bergama_strategy_sdk.fingerprints import build_decision_id
from bergama_strategy_sdk.manifest import StrategyPluginManifest
from bergama_strategy_sdk.permissions import PluginPermissions
from bergama_strategy_sdk.state import PreviousStrategyState
from bergama_strategy_sdk.testing import sample_feature_snapshot
from tests.support.strategy_sdk_helpers import (
    execution_context_for_binding,
    sample_instrument_id,
)


def _v2_manifest(**overrides: object) -> StrategyPluginManifest:
    data: dict[str, object] = {
        "strategy_id": "noop",
        "strategy_version": "2.0.0",
        "sdk_schema_version": "1.0.0",
        "runtime_protocol_version": "1.0.0",
        "feature_schema_version": "1.0.0",
        "config_schema_version": "1.0.0",
        "author": "bergama",
        "package_identity": "bergama.reference.noop.v2",
        "required_features": ("EMA20", "EMA50"),
        "permissions": PluginPermissions.empty(),
        "capabilities": {"supports_replay": True},
    }
    data.update(overrides)
    return StrategyPluginManifest.model_validate(data)


class CountingStrategy:
    def __init__(self, label: str) -> None:
        self.label = label
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.completed = 0
        self.seen_versions: list[str] = []

    async def execute(
        self,
        *,
        previous_state: PreviousStrategyState | None,
        feature_snapshot: FeatureSnapshot,
        context: StrategyExecutionContext,
        config: StrategyConfig,
    ) -> StrategyExecutionOutput:
        _ = previous_state, config
        self.seen_versions.append(context.strategy_version)
        self.started.set()
        await self.release.wait()
        self.completed += 1
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
            safe_metadata={"label": self.label},
        )
        return StrategyExecutionOutput(decision=decision, next_state=None)


class GateStrategy:
    """Strategy with explicit lifecycle gates for deterministic cancellation tests."""

    def __init__(self, label: str) -> None:
        self.label = label
        self.lease_acquired = asyncio.Event()
        self.allow_execute = asyncio.Event()
        self.dispose_started = asyncio.Event()
        self.completed = 0

    async def execute(
        self,
        *,
        previous_state: PreviousStrategyState | None,
        feature_snapshot: FeatureSnapshot,
        context: StrategyExecutionContext,
        config: StrategyConfig,
    ) -> StrategyExecutionOutput:
        _ = previous_state, config
        self.lease_acquired.set()
        await self.allow_execute.wait()
        self.completed += 1
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
            safe_metadata={"label": self.label},
        )
        return StrategyExecutionOutput(decision=decision, next_state=None)


def _session_with(
    *,
    old: CountingStrategy | GateStrategy | SdkNoOpStrategy,
    new: CountingStrategy | GateStrategy | SdkNoOpStrategy | None = None,
    v2: StrategyPluginManifest | None = None,
) -> tuple:
    registry = StrategySdkPluginRegistry()
    v1 = reference_plugin_manifest()
    registry.register(v1, lambda _m: old)
    resolved_v2 = v2 if v2 is not None else _v2_manifest()
    if new is not None:
        registry.register(resolved_v2, lambda _m: new)
    engine = build_strategy_sdk_runtime_engine(
        registry=registry,
        feature_registry=build_reference_feature_registry(),
        compatibility_policy=reference_runtime_policy(),
        decision_port=InMemoryStrategyDecisionPort(),
    )
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        plugins=((v1, reference_strategy_config(), "noop:aapl:v1"),),
    )
    return session, resolved_v2


def test_production_replace_plugin_requires_registry_factory() -> None:
    params = inspect.signature(StrategySdkRuntimeSession.replace_plugin).parameters
    assert "strategy" not in params


@pytest.mark.asyncio
async def test_successful_replacement_creates_via_registered_factory() -> None:
    old = CountingStrategy("old")
    new = CountingStrategy("new")
    old.release.set()
    new.release.set()
    session, v2 = _session_with(old=old, new=new)
    replaced = await session.replace_plugin(
        strategy_id="noop",
        manifest=v2,
        config=reference_strategy_config(),
        strategy_instance_id="noop:aapl:v2",
    )
    assert replaced.lifecycle.health is PluginHealth.READY
    assert replaced.lifecycle.strategy is new
    snapshot = sample_feature_snapshot()
    context = execution_context_for_binding(replaced, snapshot=snapshot)
    result = await session.evaluate_batch(
        feature_snapshot=snapshot,
        instrument_id=sample_instrument_id(),
        contexts={"noop": context},
    )
    assert result.decisions[0].safe_metadata["label"] == "new"
    assert new.completed == 1
    assert session.metrics.snapshot()["plugin_replaced_total"] == 1
    events = [entry.event for entry in session.audit_sink.lifecycle_events]
    assert events == [
        "REPLACEMENT_REQUESTED",
        "INITIALIZING",
        "NEW_INSTANCE_CREATED",
        "COMPATIBILITY_VALIDATED",
        "INITIALIZED",
        "CUTOVER_STARTED",
        "CUTOVER_COMPLETED",
        "OLD_INSTANCE_DRAINING",
        "OLD_INSTANCE_DISPOSING",
        "OLD_INSTANCE_DISPOSED",
        "REPLACEMENT_COMPLETED",
    ]


@pytest.mark.asyncio
async def test_in_flight_old_execution_completes_before_old_dispose() -> None:
    old = CountingStrategy("old")
    new = CountingStrategy("new")
    new.release.set()
    session, v2 = _session_with(old=old, new=new)
    old_binding = session.bindings[0]
    snapshot = sample_feature_snapshot()
    contexts = {"noop": execution_context_for_binding(old_binding, snapshot=snapshot)}
    eval_task = asyncio.create_task(
        session.evaluate_batch(
            feature_snapshot=snapshot,
            instrument_id=sample_instrument_id(),
            contexts=contexts,
        )
    )
    await old.started.wait()
    replace_task = asyncio.create_task(
        session.replace_plugin(
            strategy_id="noop",
            manifest=v2,
            config=reference_strategy_config(),
            strategy_instance_id="noop:aapl:v2",
        )
    )
    await asyncio.wait_for(_wait_until(lambda: session.bindings[0] is not old_binding), timeout=1)
    assert session.bindings[0].lifecycle.strategy is new
    assert old_binding.leases == 1
    old.release.set()
    result = await eval_task
    replaced = await replace_task
    assert result.decisions[0].safe_metadata["label"] == "old"
    assert old.completed == 1
    assert old_binding.lifecycle.health is PluginHealth.DISPOSED
    assert replaced.lifecycle.health is PluginHealth.READY
    assert session.bindings[0] is replaced


@pytest.mark.asyncio
async def test_evaluate_after_cutover_routes_to_new_instance() -> None:
    old = CountingStrategy("old")
    new = CountingStrategy("new")
    old.release.set()
    new.release.set()
    session, v2 = _session_with(old=old, new=new)
    replaced = await session.replace_plugin(
        strategy_id="noop",
        manifest=v2,
        config=reference_strategy_config(),
        strategy_instance_id="noop:aapl:v2",
    )
    snapshot = sample_feature_snapshot()
    result = await session.evaluate_batch(
        feature_snapshot=snapshot,
        instrument_id=sample_instrument_id(),
        contexts={"noop": execution_context_for_binding(replaced, snapshot=snapshot)},
    )
    assert result.decisions[0].safe_metadata["label"] == "new"


@pytest.mark.asyncio
async def test_stale_context_after_cutover_fails_closed() -> None:
    old = CountingStrategy("old")
    new = CountingStrategy("new")
    old.release.set()
    new.release.set()
    session, v2 = _session_with(old=old, new=new)
    old_binding = session.bindings[0]
    snapshot = sample_feature_snapshot()
    stale = execution_context_for_binding(old_binding, snapshot=snapshot)
    await session.replace_plugin(
        strategy_id="noop",
        manifest=v2,
        config=reference_strategy_config(),
        strategy_instance_id="noop:aapl:v2",
    )
    with pytest.raises(StrategyContractViolation) as exc:
        await session.evaluate_batch(
            feature_snapshot=snapshot,
            instrument_id=sample_instrument_id(),
            contexts={"noop": stale},
        )
    assert exc.value.detail is not None
    assert "binding_context_mismatch" in exc.value.detail
    assert new.completed == 0


@pytest.mark.asyncio
async def test_compatibility_failure_preserves_old_ready_instance() -> None:
    session, _ = _session_with(old=SdkNoOpStrategy(), new=None)
    old = session.bindings[0]
    bad = _v2_manifest(required_features=("MISSING_FEATURE",))
    session.register_factory_for_tests(manifest=bad, strategy=SdkNoOpStrategy())
    with pytest.raises(StrategyFeatureSchemaError):
        await session.replace_plugin(
            strategy_id="noop",
            manifest=bad,
            config=reference_strategy_config(),
            strategy_instance_id="noop:aapl:bad",
        )
    assert session.bindings[0] is old
    assert old.lifecycle.health is PluginHealth.READY
    assert session.metrics.snapshot()["plugin_replace_rejected_total"] == 1
    events = [entry.event for entry in session.audit_sink.lifecycle_events]
    assert events[0] == "REPLACEMENT_REQUESTED"
    assert "INCOMPATIBLE" in events
    assert events[-1] == "REPLACE_REJECTED"


@pytest.mark.asyncio
async def test_initialization_failure_preserves_old_ready_instance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session, v2 = _session_with(old=SdkNoOpStrategy(), new=SdkNoOpStrategy())
    old = session.bindings[0]

    def boom(
        self: PluginLifecycle,
        *,
        strategy: object,
        registry: object,
        policy: object,
        budgets: object,
    ) -> None:
        _ = strategy, registry, policy, budgets
        self.health = PluginHealth.INITIALIZING
        raise RuntimeError("initialize boom")

    monkeypatch.setattr(PluginLifecycle, "initialize", boom)
    with pytest.raises(RuntimeError, match="initialize boom"):
        await session.replace_plugin(
            strategy_id="noop",
            manifest=v2,
            config=reference_strategy_config(),
            strategy_instance_id="noop:aapl:v2",
        )
    assert session.bindings[0] is old
    assert old.lifecycle.health is PluginHealth.READY
    events = [entry.event for entry in session.audit_sink.lifecycle_events]
    assert events[0] == "REPLACEMENT_REQUESTED"
    assert events[-1] == "REPLACE_REJECTED"


@pytest.mark.asyncio
async def test_version_incompatibility_preserves_old_instance() -> None:
    registry = StrategySdkPluginRegistry()
    v1 = reference_plugin_manifest()
    bad = _v2_manifest(sdk_schema_version="2.0.0")
    registry.register(v1, lambda _m: SdkNoOpStrategy())
    registry.register(bad, lambda _m: SdkNoOpStrategy())
    engine = build_strategy_sdk_runtime_engine(
        registry=registry,
        feature_registry=build_reference_feature_registry(),
        compatibility_policy=RuntimeCompatibilityPolicy(sdk_schema_version="1.0.0"),
        decision_port=InMemoryStrategyDecisionPort(),
    )
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        plugins=((v1, reference_strategy_config(), "noop:aapl:v1"),),
    )
    old = session.bindings[0]
    with pytest.raises(StrategyCompatibilityError):
        await session.replace_plugin(
            strategy_id="noop",
            manifest=bad,
            config=reference_strategy_config(),
            strategy_instance_id="noop:aapl:bad",
        )
    assert session.bindings[0] is old
    assert old.lifecycle.health is PluginHealth.READY


@pytest.mark.asyncio
async def test_cancel_before_cutover_preserves_old_and_disposes_new() -> None:
    old = GateStrategy("old")
    new = GateStrategy("new")
    new.allow_execute.set()
    session, v2 = _session_with(old=old, new=new)
    old_binding = session.bindings[0]
    snapshot = sample_feature_snapshot()
    initialized = asyncio.Event()
    created: list[PluginLifecycle] = []
    original_init = PluginLifecycle.initialize

    def tracking_init(
        self: PluginLifecycle,
        *,
        strategy: object,
        registry: object,
        policy: object,
        budgets: object,
    ) -> None:
        original_init(self, strategy=strategy, registry=registry, policy=policy, budgets=budgets)
        created.append(self)
        initialized.set()

    import app.strategy.sdk_runtime.lifecycle as lifecycle_mod

    lifecycle_mod.PluginLifecycle.initialize = tracking_init  # type: ignore[method-assign]
    try:
        eval_task = asyncio.create_task(
            session.evaluate_batch(
                feature_snapshot=snapshot,
                instrument_id=sample_instrument_id(),
                contexts={"noop": execution_context_for_binding(old_binding, snapshot=snapshot)},
            )
        )
        await old.lease_acquired.wait()
        assert old_binding.leases == 1
        routing_lock = session._routing_locks["noop"]
        await routing_lock.acquire()
        try:
            replace_task = asyncio.create_task(
                session.replace_plugin(
                    strategy_id="noop",
                    manifest=v2,
                    config=reference_strategy_config(),
                    strategy_instance_id="noop:aapl:v2",
                )
            )
            await initialized.wait()
            assert created
            new_lifecycle = created[0]
            assert new_lifecycle.health is PluginHealth.READY
            replace_task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await replace_task
            assert session.bindings[0] is old_binding
            assert new_lifecycle.health is PluginHealth.DISPOSED
            assert old_binding.lifecycle.health is PluginHealth.READY
        finally:
            routing_lock.release()
        old.allow_execute.set()
        result = await eval_task
        assert result.decisions[0].safe_metadata["label"] == "old"
    finally:
        lifecycle_mod.PluginLifecycle.initialize = original_init  # type: ignore[method-assign]


@pytest.mark.asyncio
async def test_cancel_after_cutover_keeps_new_and_disposes_old() -> None:
    old = GateStrategy("old")
    new = GateStrategy("new")
    new.allow_execute.set()
    session, v2 = _session_with(old=old, new=new)
    old_binding = session.bindings[0]
    snapshot = sample_feature_snapshot()
    eval_task = asyncio.create_task(
        session.evaluate_batch(
            feature_snapshot=snapshot,
            instrument_id=sample_instrument_id(),
            contexts={"noop": execution_context_for_binding(old_binding, snapshot=snapshot)},
        )
    )
    await old.lease_acquired.wait()
    replace_task = asyncio.create_task(
        session.replace_plugin(
            strategy_id="noop",
            manifest=v2,
            config=reference_strategy_config(),
            strategy_instance_id="noop:aapl:v2",
        )
    )
    await asyncio.wait_for(_wait_until(lambda: session.bindings[0] is not old_binding), timeout=1)
    new_binding = session.bindings[0]
    replace_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await replace_task
    assert session.bindings[0] is new_binding
    assert new_binding.lifecycle.health is PluginHealth.READY
    old.allow_execute.set()
    await eval_task
    await asyncio.wait_for(
        _wait_until(lambda: old_binding.lifecycle.health is PluginHealth.DISPOSED),
        timeout=1,
    )
    await session.aclose()
    assert old_binding.lifecycle.health is PluginHealth.DISPOSED


@pytest.mark.asyncio
async def test_cancel_while_multiple_old_leases_drain() -> None:
    old = GateStrategy("old")
    new = GateStrategy("new")
    new.allow_execute.set()
    session, v2 = _session_with(old=old, new=new)
    old_binding = session.bindings[0]
    snapshot = sample_feature_snapshot()
    ctx = execution_context_for_binding(old_binding, snapshot=snapshot)
    first = asyncio.create_task(
        session.evaluate_batch(
            feature_snapshot=snapshot,
            instrument_id=sample_instrument_id(),
            contexts={"noop": ctx},
        )
    )
    await old.lease_acquired.wait()
    # Second lease on same binding via direct acquire while first holds lock in execute.
    second_lease = await session._acquire_ready_lease("noop")
    assert second_lease is old_binding
    assert old_binding.leases == 2
    replace_task = asyncio.create_task(
        session.replace_plugin(
            strategy_id="noop",
            manifest=v2,
            config=reference_strategy_config(),
            strategy_instance_id="noop:aapl:v2",
        )
    )
    await asyncio.wait_for(_wait_until(lambda: session.bindings[0] is not old_binding), timeout=1)
    replace_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await replace_task
    assert session.bindings[0].lifecycle.strategy is new
    old.allow_execute.set()
    await first
    await session._release_lease(old_binding)
    await asyncio.wait_for(
        _wait_until(lambda: old_binding.lifecycle.health is PluginHealth.DISPOSED),
        timeout=1,
    )
    await session.aclose()


@pytest.mark.asyncio
async def test_separate_instances_remain_independent_under_concurrent_evaluate() -> None:
    first = CountingStrategy("a")
    second = CountingStrategy("b")
    first.release.set()
    second.release.set()
    registry = StrategySdkPluginRegistry()
    a = reference_plugin_manifest()
    b = StrategyPluginManifest(
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
    registry.register(a, lambda _m: first)
    registry.register(b, lambda _m: second)
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
            (a, reference_strategy_config(), "noop:aapl:a"),
            (b, reference_strategy_config(), "noop2:aapl:b"),
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
    )
    assert result.execution_summary.succeeded == 2
    assert first.completed == 1
    assert second.completed == 1


@pytest.mark.asyncio
async def test_unknown_factory_rejected_and_old_preserved() -> None:
    session, v2 = _session_with(old=SdkNoOpStrategy(), new=None)
    old = session.bindings[0]
    with pytest.raises(StrategyManifestError):
        await session.replace_plugin(
            strategy_id="noop",
            manifest=v2,
            config=reference_strategy_config(),
            strategy_instance_id="noop:aapl:v2",
        )
    assert session.bindings[0] is old
    assert old.lifecycle.health is PluginHealth.READY


@pytest.mark.asyncio
async def test_replacement_between_enumeration_and_lease_is_consistent() -> None:
    old = CountingStrategy("old")
    new = CountingStrategy("new")
    old.release.set()
    new.release.set()
    session, v2 = _session_with(old=old, new=new)
    snapshot = sample_feature_snapshot()
    old_binding = session.bindings[0]
    stale = execution_context_for_binding(old_binding, snapshot=snapshot)
    await session.replace_plugin(
        strategy_id="noop",
        manifest=v2,
        config=reference_strategy_config(),
        strategy_instance_id="noop:aapl:v2",
    )
    with pytest.raises(StrategyContractViolation) as exc:
        await session.evaluate_batch(
            feature_snapshot=snapshot,
            instrument_id=sample_instrument_id(),
            contexts={"noop": stale},
        )
    assert exc.value.detail is not None
    assert "binding_context_mismatch" in exc.value.detail
    fresh = execution_context_for_binding(session.bindings[0], snapshot=snapshot)
    result = await session.evaluate_batch(
        feature_snapshot=snapshot,
        instrument_id=sample_instrument_id(),
        contexts={"noop": fresh},
    )
    assert result.decisions[0].safe_metadata["label"] == "new"
    assert new.seen_versions == ["2.0.0"]


async def _wait_until(predicate, *, interval: float = 0.0) -> None:
    while not predicate():
        await asyncio.sleep(interval)
        await asyncio.sleep(0)
