"""Strategy SDK public API freeze and contract tests (#51)."""

from __future__ import annotations

import inspect
from decimal import Decimal

import bergama_strategy_sdk
import pytest
from bergama_strategy_sdk import (
    FeatureSnapshot,
    FeatureValue,
    StrategyExecutionOutput,
)
from bergama_strategy_sdk.decisions import StrategyAction, StrategyDecision, StrategyReasonCode
from bergama_strategy_sdk.execution import Strategy
from bergama_strategy_sdk.testing import sample_execution_context, sample_feature_snapshot
from pydantic import ValidationError

FROZEN_PUBLIC_API: tuple[str, ...] = (
    "DeprecationDescriptor",
    "FeatureSnapshot",
    "FeatureValue",
    "MigrationGuidance",
    "NextStrategyState",
    "PluginCapability",
    "PluginPermissions",
    "PreviousStrategyState",
    "RuntimeCompatibilityPolicy",
    "Strategy",
    "StrategyAction",
    "StrategyCompatibilityError",
    "StrategyConfig",
    "StrategyConfigurationError",
    "StrategyContractViolation",
    "StrategyDecision",
    "StrategyExecutionContext",
    "StrategyExecutionError",
    "StrategyExecutionOutput",
    "StrategyFeatureSchemaError",
    "StrategyLifecycleError",
    "StrategyManifestError",
    "StrategyPermissionError",
    "StrategyPluginCrash",
    "StrategyPluginManifest",
    "StrategyReasonCode",
    "StrategySdkError",
    "StrategyStateError",
    "StrategyTimeoutError",
    "StrategyValidationError",
    "StrategyBudgetExceededError",
    "VersionAxes",
    "build_decision_id",
    "configuration_fingerprint",
    "execution_fingerprint",
    "feature_fingerprint",
    "state_fingerprint",
    "strategy_fingerprint",
    "validate_manifest_compatibility",
)


def test_public_sdk_root_exports_match_exact_issue_51_freeze() -> None:
    assert tuple(bergama_strategy_sdk.__all__) == FROZEN_PUBLIC_API
    assert len(bergama_strategy_sdk.__all__) == 39
    assert set(bergama_strategy_sdk.__all__) == set(FROZEN_PUBLIC_API)


def test_public_sdk_root_excludes_internal_and_runtime_symbols() -> None:
    public = set(bergama_strategy_sdk.__all__)
    assert "StrategyCancellationError" not in public
    assert "PUBLIC_API_VERSION" not in public
    assert "PluginHealth" not in public
    assert "PluginLifecycle" not in public
    assert "StrategyBatchExecutionResult" not in public
    assert "StrategyEngine" not in public
    assert "experimental" not in public

    assert not hasattr(bergama_strategy_sdk, "StrategyCancellationError")
    assert not hasattr(bergama_strategy_sdk, "PluginHealth")
    assert not hasattr(bergama_strategy_sdk, "PluginLifecycle")
    assert not hasattr(bergama_strategy_sdk, "StrategyBatchExecutionResult")
    assert not hasattr(bergama_strategy_sdk, "StrategySdkRuntimeSession")
    # Internal metadata may exist on the module object but must not be public.
    assert "PUBLIC_API_VERSION" not in public


def test_experimental_namespace_is_reserved_and_not_reexported() -> None:
    assert "experimental" not in bergama_strategy_sdk.__all__
    import bergama_strategy_sdk.experimental as experimental

    assert experimental is not None
    assert getattr(experimental, "EXPERIMENTAL_API_ENABLED", None) is False
    assert not hasattr(bergama_strategy_sdk, "EXPERIMENTAL_API_ENABLED")


def test_strategy_protocol_signature_remains_stable() -> None:
    params = inspect.signature(Strategy.execute).parameters
    assert list(params) == [
        "self",
        "previous_state",
        "feature_snapshot",
        "context",
        "config",
    ]
    assert params["previous_state"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["feature_snapshot"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["context"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["config"].kind is inspect.Parameter.KEYWORD_ONLY


def test_strategy_execution_output_remains_immutable_structured_result() -> None:
    context = sample_execution_context()
    snapshot = sample_feature_snapshot()
    decision = StrategyDecision.from_execution(
        decision_id="a" * 64,
        context=context,
        snapshot=snapshot,
        action=StrategyAction.NO_ACTION,
        confidence=1.0,
        reason_codes=(StrategyReasonCode.NO_ACTION_REFERENCE,),
        processing_latency_ms=0.0,
        occurred_at=context.evaluation_time,
        decision_timestamp=context.evaluation_time,
    )
    output = StrategyExecutionOutput(decision=decision, next_state=None)
    assert output.decision is decision
    assert output.next_state is None
    with pytest.raises(ValidationError):
        output.decision = decision  # type: ignore[misc]


def test_feature_snapshot_fingerprint_is_order_canonical_and_deterministic() -> None:
    first = FeatureSnapshot(
        feature_schema_version="1.0.0",
        instrument_key="equity:AAPL:XNYS",
        snapshot_id="snap-1",
        features=(
            FeatureValue(
                feature_id="EMA50",
                schema_id="technical",
                schema_version="1.0.0",
                value=Decimal("148.10"),
            ),
            FeatureValue(
                feature_id="EMA20",
                schema_id="technical",
                schema_version="1.0.0",
                value=Decimal("150.25"),
            ),
        ),
    )
    second = FeatureSnapshot(
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
    assert first.canonical_features == second.canonical_features
    assert first.fingerprint() == second.fingerprint()
    assert first.fingerprint() == sample_feature_snapshot().fingerprint()


def test_feature_snapshot_rejects_float_nan_and_duplicate_feature_ids() -> None:
    with pytest.raises(TypeError):
        FeatureValue(
            feature_id="EMA20",
            schema_id="technical",
            schema_version="1.0.0",
            value=1.5,  # type: ignore[arg-type]
        )
    with pytest.raises(ValidationError):
        FeatureValue(
            feature_id="EMA20",
            schema_id="technical",
            schema_version="1.0.0",
            value=Decimal("NaN"),
        )
    with pytest.raises(ValidationError):
        FeatureSnapshot(
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
                FeatureValue(
                    feature_id="EMA20",
                    schema_id="technical",
                    schema_version="1.0.0",
                    value=Decimal("2"),
                ),
            ),
        )
