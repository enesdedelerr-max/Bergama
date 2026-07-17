"""Runtime acceptance reconciliation tests for #406 blockers."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.core.strategy_sdk_settings import StrategySdkRuntimeSettings
from app.strategy.ports import InMemoryStrategyDecisionPort
from app.strategy.sdk_runtime.bootstrap import (
    build_reference_feature_registry,
    reference_plugin_manifest,
    reference_runtime_policy,
    reference_strategy_config,
)
from app.strategy.sdk_runtime.budgets import ExecutionBudgets
from app.strategy.sdk_runtime.engine import build_strategy_sdk_runtime_engine
from app.strategy.sdk_runtime.feature_assembler import FeatureAssembler
from app.strategy.sdk_runtime.feature_registry import FeatureSchemaRegistry
from app.strategy.sdk_runtime.legacy_adapter import (
    adapter_version,
    convert_legacy_strategy_input,
)
from app.strategy.sdk_runtime.metrics import StrategySdkRuntimeMetrics
from app.strategy.sdk_runtime.reference import SdkNoOpStrategy
from app.strategy.sdk_runtime.registry import StrategySdkPluginRegistry
from bergama_strategy_sdk.config import StrategyConfig
from bergama_strategy_sdk.context import StrategyExecutionContext
from bergama_strategy_sdk.decisions import StrategyAction, StrategyDecision, StrategyReasonCode
from bergama_strategy_sdk.errors import (
    StrategyBudgetExceededError,
    StrategyCompatibilityError,
    StrategyFeatureSchemaError,
    StrategyManifestError,
)
from bergama_strategy_sdk.execution import StrategyExecutionOutput
from bergama_strategy_sdk.features import FeatureSnapshot, FeatureValue
from bergama_strategy_sdk.fingerprints import build_decision_id
from bergama_strategy_sdk.manifest import StrategyPluginManifest
from bergama_strategy_sdk.permissions import PluginPermissions
from bergama_strategy_sdk.state import NextStrategyState, PreviousStrategyState
from bergama_strategy_sdk.testing import sample_feature_snapshot
from pydantic import ValidationError
from tests.support.market_data_fixtures import make_bar
from tests.support.strategy_helpers import quality_assessment
from tests.support.strategy_sdk_helpers import (
    execution_context_for_binding,
    sample_feature_values,
    sample_instrument_id,
)


def _manifest(**overrides: object) -> StrategyPluginManifest:
    data: dict[str, object] = {
        "strategy_id": "noop",
        "strategy_version": "1.0.0",
        "sdk_schema_version": "1.0.0",
        "runtime_protocol_version": "1.0.0",
        "feature_schema_version": "1.0.0",
        "config_schema_version": "1.0.0",
        "author": "bergama",
        "package_identity": "bergama.reference.noop",
        "required_features": ("EMA20", "EMA50"),
        "permissions": PluginPermissions.empty(),
        "capabilities": {"supports_replay": True},
    }
    data.update(overrides)
    return StrategyPluginManifest.model_validate(data)


def _session(
    *,
    strategy: object | None = None,
    budgets: ExecutionBudgets | None = None,
    manifest: StrategyPluginManifest | None = None,
    feature_registry: FeatureSchemaRegistry | None = None,
):
    registry = StrategySdkPluginRegistry()
    resolved = manifest if manifest is not None else reference_plugin_manifest()
    registry.register(resolved, lambda _m: strategy if strategy is not None else SdkNoOpStrategy())
    engine = build_strategy_sdk_runtime_engine(
        registry=registry,
        feature_registry=(
            feature_registry if feature_registry is not None else build_reference_feature_registry()
        ),
        compatibility_policy=reference_runtime_policy(),
        decision_port=InMemoryStrategyDecisionPort(),
        budgets=budgets if budgets is not None else ExecutionBudgets(),
    )
    return engine.create_session(
        run_id="run-1",
        session_id="session-1",
        plugins=((resolved, reference_strategy_config(), "noop:aapl:primary"),),
    )


class RecordingStrategy:
    def __init__(self) -> None:
        self.calls = 0

    async def execute(
        self,
        *,
        previous_state: PreviousStrategyState | None,
        feature_snapshot: FeatureSnapshot,
        context: StrategyExecutionContext,
        config: StrategyConfig,
    ) -> StrategyExecutionOutput:
        _ = previous_state, config
        self.calls += 1
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
        )
        return StrategyExecutionOutput(decision=decision, next_state=None)


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
        raise RuntimeError("plugin boom")


# --- Blocker 1: feature schema validation ---


@pytest.mark.asyncio
async def test_exact_registered_schema_accepted_and_plugin_runs() -> None:
    strategy = RecordingStrategy()
    session = _session(strategy=strategy)
    snapshot = sample_feature_snapshot()
    result = await session.evaluate_batch(
        feature_snapshot=snapshot,
        instrument_id=sample_instrument_id(),
        contexts={"noop": execution_context_for_binding(session.bindings[0], snapshot=snapshot)},
    )
    assert strategy.calls == 1
    assert result.execution_summary.succeeded == 1


@pytest.mark.asyncio
async def test_unknown_schema_id_rejected_before_plugin() -> None:
    strategy = RecordingStrategy()
    session = _session(strategy=strategy)
    snapshot = sample_feature_snapshot().model_copy(
        update={
            "features": (
                FeatureValue(
                    feature_id="EMA20",
                    schema_id="unknown",
                    schema_version="1.0.0",
                    value=Decimal("1"),
                ),
                FeatureValue(
                    feature_id="EMA50",
                    schema_id="unknown",
                    schema_version="1.0.0",
                    value=Decimal("2"),
                ),
            )
        }
    )
    with pytest.raises(StrategyFeatureSchemaError):
        await session.evaluate_batch(
            feature_snapshot=snapshot,
            instrument_id=sample_instrument_id(),
            contexts={
                "noop": execution_context_for_binding(session.bindings[0], snapshot=snapshot)
            },
        )
    assert strategy.calls == 0
    assert session.metrics.snapshot()["feature_schema_rejection_total"] == 1


@pytest.mark.asyncio
async def test_wrong_schema_version_rejected() -> None:
    strategy = RecordingStrategy()
    session = _session(strategy=strategy)
    snapshot = sample_feature_snapshot().model_copy(
        update={
            "features": tuple(
                feature.model_copy(update={"schema_version": "9.9.9"})
                for feature in sample_feature_snapshot().features
            )
        }
    )
    with pytest.raises(StrategyFeatureSchemaError):
        await session.evaluate_batch(
            feature_snapshot=snapshot,
            instrument_id=sample_instrument_id(),
            contexts={
                "noop": execution_context_for_binding(session.bindings[0], snapshot=snapshot)
            },
        )
    assert strategy.calls == 0


@pytest.mark.asyncio
async def test_manifest_schema_version_mismatch_rejected() -> None:
    strategy = RecordingStrategy()
    session = _session(strategy=strategy)
    snapshot = sample_feature_snapshot().model_copy(update={"feature_schema_version": "9.0.0"})
    with pytest.raises(StrategyFeatureSchemaError):
        await session.evaluate_batch(
            feature_snapshot=snapshot,
            instrument_id=sample_instrument_id(),
            contexts={
                "noop": execution_context_for_binding(session.bindings[0], snapshot=snapshot)
            },
        )
    assert strategy.calls == 0


@pytest.mark.asyncio
async def test_missing_required_feature_rejected() -> None:
    strategy = RecordingStrategy()
    session = _session(strategy=strategy)
    snapshot = FeatureSnapshot(
        feature_schema_version="1.0.0",
        instrument_key="equity:AAPL:XNYS",
        snapshot_id="snap-1",
        features=(
            FeatureValue(
                feature_id="EMA20",
                schema_id="technical",
                schema_version="1.0.0",
                value=Decimal("1"),
            ),
        ),
    )
    with pytest.raises(StrategyFeatureSchemaError) as exc:
        await session.evaluate_batch(
            feature_snapshot=snapshot,
            instrument_id=sample_instrument_id(),
            contexts={
                "noop": execution_context_for_binding(session.bindings[0], snapshot=snapshot)
            },
        )
    assert exc.value.detail == "missing_required_feature:EMA50"
    assert strategy.calls == 0


@pytest.mark.asyncio
async def test_unknown_feature_rejected_when_schema_closed() -> None:
    strategy = RecordingStrategy()
    session = _session(strategy=strategy)
    snapshot = sample_feature_snapshot().model_copy(
        update={
            "features": (
                *sample_feature_snapshot().features,
                FeatureValue(
                    feature_id="UNKNOWN_X",
                    schema_id="technical",
                    schema_version="1.0.0",
                    value=Decimal("1"),
                ),
            )
        }
    )
    with pytest.raises(StrategyFeatureSchemaError):
        await session.evaluate_batch(
            feature_snapshot=snapshot,
            instrument_id=sample_instrument_id(),
            contexts={
                "noop": execution_context_for_binding(session.bindings[0], snapshot=snapshot)
            },
        )
    assert strategy.calls == 0


def test_schema_validation_is_deterministic() -> None:
    registry = build_reference_feature_registry()
    manifest = reference_plugin_manifest()
    snapshot = sample_feature_snapshot()
    registry.validate_snapshot(snapshot, manifest=manifest)
    registry.validate_snapshot(snapshot, manifest=manifest)
    assert registry.fingerprint() == build_reference_feature_registry().fingerprint()


# --- Blocker 2: strict capabilities ---


@pytest.mark.parametrize("value", [True, False])
def test_capability_exact_bool_accepted(value: bool) -> None:
    if value is False:
        with pytest.raises(ValidationError):
            _manifest(capabilities={"supports_replay": False})
        return
    manifest = _manifest(capabilities={"supports_replay": True})
    assert manifest.capabilities["supports_replay"] is True
    assert manifest.fingerprint() == _manifest(capabilities={"supports_replay": True}).fingerprint()


@pytest.mark.parametrize(
    "value",
    [1, 0, "true", "false", 1.0, None, [], {"a": 1}],
)
def test_capability_non_bool_rejected(value: object) -> None:
    with pytest.raises((ValidationError, TypeError)):
        _manifest(capabilities={"supports_replay": value})


def test_unknown_capability_and_training_rejected() -> None:
    with pytest.raises(ValidationError):
        _manifest(capabilities={"supports_replay": True, "unknown_cap": True})
    with pytest.raises(ValidationError):
        _manifest(capabilities={"supports_replay": True, "supports_training": True})


# --- Blocker 3+4: budgets ---


def test_budget_matrix_below_exact_above() -> None:
    manifest = reference_plugin_manifest()
    snapshot = sample_feature_snapshot()
    config = StrategyConfig(config_schema_version="1.0.0", safe_metadata={"a": "1"})
    state = PreviousStrategyState(
        state_schema_version="1.0.0",
        state_id="s1",
        payload={"step": "1"},
    )
    next_state = NextStrategyState(
        state_schema_version="1.0.0",
        state_id="s2",
        payload={"step": "2"},
    )

    # feature payload
    exact_feature = ExecutionBudgets(max_feature_payload_bytes=snapshot.payload_byte_length())
    exact_feature.validate_feature_snapshot(snapshot)
    with pytest.raises(StrategyBudgetExceededError) as feature_exc:
        ExecutionBudgets(
            max_feature_payload_bytes=snapshot.payload_byte_length() - 1
        ).validate_feature_snapshot(snapshot)
    assert feature_exc.value.detail == "feature_payload"

    # manifest / required features
    exact_manifest = ExecutionBudgets(
        max_manifest_bytes=len(manifest.model_dump_json().encode("utf-8"))
    )
    exact_manifest.validate_manifest(manifest)
    with pytest.raises(StrategyBudgetExceededError) as manifest_exc:
        ExecutionBudgets(max_manifest_bytes=8).validate_manifest(manifest)
    assert manifest_exc.value.detail == "manifest"
    exact_req = ExecutionBudgets(max_required_features=len(manifest.required_features))
    exact_req.validate_manifest(manifest)
    with pytest.raises(StrategyBudgetExceededError) as req_exc:
        ExecutionBudgets(max_required_features=1).validate_manifest(manifest)
    assert req_exc.value.detail == "required_features"

    # config / safe metadata
    encoded = str(dict(sorted(config.safe_metadata.items()))).encode("utf-8")
    ExecutionBudgets(max_safe_metadata_bytes=len(encoded)).validate_config(config)
    with pytest.raises(StrategyBudgetExceededError) as meta_exc:
        ExecutionBudgets(max_safe_metadata_bytes=len(encoded) - 1).validate_config(config)
    assert meta_exc.value.detail == "safe_metadata"

    # previous / next state
    state_bytes = len(state.model_dump_json().encode("utf-8"))
    ExecutionBudgets(max_state_bytes=state_bytes).validate_state(state)
    with pytest.raises(StrategyBudgetExceededError) as state_exc:
        ExecutionBudgets(max_state_bytes=state_bytes - 1).validate_state(state)
    assert state_exc.value.detail == "state"
    next_bytes = len(next_state.model_dump_json().encode("utf-8"))
    ExecutionBudgets(max_state_bytes=next_bytes).validate_state(next_state)
    with pytest.raises(StrategyBudgetExceededError) as next_exc:
        ExecutionBudgets(max_state_bytes=next_bytes - 1).validate_state(next_state)
    assert next_exc.value.detail == "state"

    # failure metadata
    meta = {"code": "x"}
    meta_bytes = len(str(dict(sorted(meta.items()))).encode("utf-8"))
    ExecutionBudgets(max_safe_metadata_bytes=meta_bytes).validate_failure_metadata(meta)
    with pytest.raises(StrategyBudgetExceededError) as fail_meta_exc:
        ExecutionBudgets(max_safe_metadata_bytes=meta_bytes - 1).validate_failure_metadata(meta)
    assert fail_meta_exc.value.detail == "runtime_failure_metadata"

    # failure count
    budgets = ExecutionBudgets(max_plugin_failures_per_batch=2)
    budgets.validate_failure_count(0)
    budgets.validate_failure_count(2)
    with pytest.raises(StrategyBudgetExceededError) as count_exc:
        budgets.validate_failure_count(3)
    assert count_exc.value.detail == "plugin_failures_per_batch"


@pytest.mark.asyncio
async def test_failure_count_budget_enforced_on_consecutive_failures() -> None:
    registry = StrategySdkPluginRegistry()
    manifests = [
        _manifest(strategy_id=f"fail{i}", package_identity=f"pkg.fail{i}") for i in range(4)
    ]
    for manifest in manifests:
        registry.register(manifest, lambda _m: CrashingStrategy())
    engine = build_strategy_sdk_runtime_engine(
        registry=registry,
        feature_registry=build_reference_feature_registry(),
        compatibility_policy=reference_runtime_policy(),
        decision_port=InMemoryStrategyDecisionPort(),
        budgets=ExecutionBudgets(max_plugin_failures_per_batch=2),
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
    with pytest.raises(StrategyBudgetExceededError) as exc:
        await session.evaluate_batch(
            feature_snapshot=snapshot,
            instrument_id=sample_instrument_id(),
            contexts=contexts,
        )
    assert exc.value.detail == "plugin_failures_per_batch"
    assert session.bindings[0].lifecycle.health.value == "DISABLED"
    assert session.bindings[1].lifecycle.health.value == "DISABLED"
    assert session.bindings[2].lifecycle.health.value == "DISABLED"
    # Fourth plugin must not have been evaluated after budget breach at count=3.
    assert session.bindings[3].lifecycle.health.value == "READY"
    assert session.metrics.snapshot()["budget_violation_total"] >= 1


@pytest.mark.asyncio
async def test_output_and_timeout_budgets_preserve_typed_errors() -> None:
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
                safe_metadata={"blob": "z" * 200},
            )
            return StrategyExecutionOutput(decision=decision, next_state=None)

    session = _session(
        strategy=FatStrategy(),
        budgets=ExecutionBudgets(max_safe_metadata_bytes=32, max_output_bytes=10_000),
    )
    snapshot = sample_feature_snapshot()
    result = await session.evaluate_batch(
        feature_snapshot=snapshot,
        instrument_id=sample_instrument_id(),
        contexts={"noop": execution_context_for_binding(session.bindings[0], snapshot=snapshot)},
    )
    assert result.plugin_failures[0].failure_type == "StrategyBudgetExceededError"


# --- Blocker 5: registry identity ---


def test_registry_manifest_identity_binding() -> None:
    registry = StrategySdkPluginRegistry()
    base = reference_plugin_manifest()
    calls: list[str] = []

    def factory(manifest: StrategyPluginManifest) -> SdkNoOpStrategy:
        calls.append(manifest.fingerprint())
        return SdkNoOpStrategy()

    registry.register(base, factory)
    created = registry.create(base)
    assert isinstance(created, SdkNoOpStrategy)
    assert len(calls) == 1

    different_fp = _manifest(author="other-author")
    with pytest.raises(StrategyManifestError) as fp_exc:
        registry.create(different_fp)
    assert fp_exc.value.detail is not None
    assert "manifest_identity_mismatch" in fp_exc.value.detail
    assert len(calls) == 1

    different_pkg = _manifest(package_identity="other.package")
    with pytest.raises(StrategyManifestError) as pkg_exc:
        registry.create(different_pkg)
    assert pkg_exc.value.detail is not None
    assert "manifest_identity_mismatch" in pkg_exc.value.detail

    version_axis = _manifest(feature_schema_version="2.0.0")
    with pytest.raises(StrategyManifestError) as axis_exc:
        registry.create(version_axis)
    assert axis_exc.value.detail is not None
    assert "manifest_identity_mismatch" in axis_exc.value.detail

    with pytest.raises(StrategyManifestError):
        registry.register(base, factory)
    with pytest.raises(StrategyManifestError) as conflict_exc:
        registry.register(_manifest(author="alt"), factory)
    assert conflict_exc.value.detail is not None
    assert "conflicting_plugin_identity" in conflict_exc.value.detail


# --- Blocker 10: legacy adapter ---


def test_legacy_adapter_disabled_by_default_and_explicit_enablement() -> None:
    settings = StrategySdkRuntimeSettings()
    assert settings.legacy_adapter_enabled is False
    assert adapter_version() == "1.0.0"
    event = make_bar()
    from app.market_data.keys import build_deduplication_key, build_idempotency_key
    from app.strategy.models import QualitySummary, StrategyInput

    assessment = quality_assessment(event)
    strategy_input = StrategyInput(
        event=event,
        instrument_id=event.instrument,
        run_id="run-1",
        session_id="session-1",
        idempotency_key=build_idempotency_key(event),
        deduplication_key=build_deduplication_key(event),
        quality_summary=QualitySummary.from_event_and_assessment(
            event=event, assessment=assessment
        ),
        received_at=event.ingested_at,
    )
    assembler = FeatureAssembler(
        registry=build_reference_feature_registry(),
        feature_schema_version="1.0.0",
    )
    metrics = StrategySdkRuntimeMetrics()
    with pytest.raises(StrategyCompatibilityError) as disabled_exc:
        convert_legacy_strategy_input(
            strategy_input,
            settings=settings,
            assembler=assembler,
            required_features=("EMA20", "EMA50"),
            feature_values=sample_feature_values(),
            host_instrument_id=event.instrument,
            metrics=metrics,
        )
    assert disabled_exc.value.detail == "legacy_adapter_disabled"
    enabled = StrategySdkRuntimeSettings(legacy_adapter_enabled=True)
    snapshot = convert_legacy_strategy_input(
        strategy_input,
        settings=enabled,
        assembler=assembler,
        required_features=("EMA20", "EMA50"),
        feature_values=sample_feature_values(),
        host_instrument_id=event.instrument,
        metrics=metrics,
    )
    assert snapshot.features[0].schema_id == "technical"
    assert (
        snapshot.fingerprint()
        == convert_legacy_strategy_input(
            strategy_input,
            settings=enabled,
            assembler=assembler,
            required_features=("EMA20", "EMA50"),
            feature_values=sample_feature_values(),
            host_instrument_id=event.instrument,
        ).fingerprint()
    )
    with pytest.raises(StrategyFeatureSchemaError):
        convert_legacy_strategy_input(
            strategy_input,
            settings=enabled,
            assembler=assembler,
            required_features=("EMA20", "EMA50"),
            feature_values={"EMA20": Decimal("1")},
            host_instrument_id=event.instrument,
            metrics=metrics,
        )
    assert metrics.feature_assembly_error_total == 1


# --- Blocker 11: metrics emission ---


@pytest.mark.asyncio
async def test_declared_metrics_are_emitted() -> None:
    session = _session(strategy=CrashingStrategy())
    snapshot = sample_feature_snapshot()
    result = await session.evaluate_batch(
        feature_snapshot=snapshot,
        instrument_id=sample_instrument_id(),
        contexts={"noop": execution_context_for_binding(session.bindings[0], snapshot=snapshot)},
    )
    metrics = session.metrics.snapshot()
    assert result.execution_summary.failed == 1
    assert metrics["plugin_failed_total"] == 1
    assert metrics["plugin_disabled_total"] == 1
    assert metrics["plugin_crash_total"] == 1
    assert "feature_schema_rejection_total" in metrics
    assert "feature_assembly_error_total" in metrics
