"""Strategy SDK model and fingerprint tests (#406)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from bergama_strategy_sdk.config import StrategyConfig
from bergama_strategy_sdk.context import StrategyExecutionContext
from bergama_strategy_sdk.deprecation import DeprecationDescriptor
from bergama_strategy_sdk.features import FeatureSnapshot, FeatureValue
from bergama_strategy_sdk.fingerprints import (
    build_decision_id,
    configuration_fingerprint,
    execution_fingerprint,
    feature_fingerprint,
    strategy_fingerprint,
)
from bergama_strategy_sdk.manifest import StrategyPluginManifest
from bergama_strategy_sdk.permissions import PluginPermissions
from bergama_strategy_sdk.testing import (
    sample_config,
    sample_execution_context,
    sample_feature_snapshot,
)
from pydantic import ValidationError


class ExtendedStrategyConfig(StrategyConfig):
    window: int = 20


def test_feature_snapshot_is_strict_immutable_and_duplicate_rejected() -> None:
    snapshot = sample_feature_snapshot()
    assert snapshot.fingerprint() == sample_feature_snapshot().fingerprint()
    with pytest.raises(ValidationError):
        FeatureSnapshot(
            feature_schema_version="1.0.0",
            instrument_key="equity:AAPL:XNYS",
            snapshot_id="snap-1",
            features=(
                FeatureValue(
                    feature_id="EMA20",
                    schema_id="ema",
                    schema_version="1.0.0",
                    value=Decimal("1"),
                ),
                FeatureValue(
                    feature_id="EMA20",
                    schema_id="ema",
                    schema_version="1.0.0",
                    value=Decimal("2"),
                ),
            ),
        )


def test_safe_metadata_excluded_from_configuration_and_execution_fingerprints() -> None:
    config_a = StrategyConfig(config_schema_version="1.0.0", safe_metadata={"a": "1"})
    config_b = StrategyConfig(config_schema_version="1.0.0", safe_metadata={"b": "2"})
    assert config_a.fingerprint() == config_b.fingerprint()
    snapshot = sample_feature_snapshot()
    ctx_a = sample_execution_context(snapshot=snapshot, config=config_a)
    ctx_b = sample_execution_context(snapshot=snapshot, config=config_b)
    assert ctx_a.configuration_fingerprint == ctx_b.configuration_fingerprint
    assert ctx_a.execution_fingerprint == ctx_b.execution_fingerprint
    assert build_decision_id(
        strategy_id=ctx_a.strategy_id,
        strategy_version=ctx_a.strategy_version,
        strategy_instance_id=ctx_a.strategy_instance_id,
        run_id=ctx_a.run_id,
        execution_fingerprint_value=ctx_a.execution_fingerprint,
        action="NO_ACTION",
        runtime_protocol_version=ctx_a.runtime_protocol_version,
    ) == build_decision_id(
        strategy_id=ctx_b.strategy_id,
        strategy_version=ctx_b.strategy_version,
        strategy_instance_id=ctx_b.strategy_instance_id,
        run_id=ctx_b.run_id,
        execution_fingerprint_value=ctx_b.execution_fingerprint,
        action="NO_ACTION",
        runtime_protocol_version=ctx_b.runtime_protocol_version,
    )


def test_business_config_change_changes_configuration_fingerprint() -> None:
    left = ExtendedStrategyConfig(config_schema_version="1.0.0", window=10)
    right = ExtendedStrategyConfig(config_schema_version="1.0.0", window=20)
    assert left.fingerprint() != right.fingerprint()


def test_configuration_fingerprint_is_order_stable() -> None:
    first = StrategyConfig(config_schema_version="1.0.0", safe_metadata={"z": "1", "a": "2"})
    second = StrategyConfig(config_schema_version="1.0.0", safe_metadata={"a": "2", "z": "1"})
    assert first.fingerprint_payload() == second.fingerprint_payload()
    assert first.fingerprint() == second.fingerprint()


def test_config_and_feature_fingerprints_are_independent() -> None:
    config = sample_config()
    snapshot = sample_feature_snapshot()
    feature_fp = feature_fingerprint(snapshot.fingerprint_payload())
    assert feature_fp == snapshot.fingerprint()
    assert configuration_fingerprint(config.fingerprint_payload()) != feature_fp


def test_execution_fingerprint_composes_without_collapsing() -> None:
    snapshot = sample_feature_snapshot()
    config = StrategyConfig(config_schema_version="1.0.0")
    strategy_fp = strategy_fingerprint(
        strategy_id="noop",
        strategy_version="1.0.0",
        strategy_instance_id="noop:aapl:primary",
        sdk_schema_version="1.0.0",
    )
    feature_fp = snapshot.fingerprint()
    config_fp = config.fingerprint()
    execution_fp = execution_fingerprint(
        strategy_fingerprint_value=strategy_fp,
        feature_fingerprint_value=feature_fp,
        configuration_fingerprint_value=config_fp,
        runtime_protocol_version="1.0.0",
        previous_state_fingerprint=None,
    )
    assert execution_fp != strategy_fp
    assert execution_fp != feature_fp
    assert execution_fp != config_fp


def test_manifest_rejects_unknown_and_training_capabilities() -> None:
    with pytest.raises(ValidationError):
        StrategyPluginManifest(
            strategy_id="noop",
            strategy_version="1.0.0",
            sdk_schema_version="1.0.0",
            runtime_protocol_version="1.0.0",
            feature_schema_version="1.0.0",
            config_schema_version="1.0.0",
            author="bergama",
            package_identity="pkg",
            permissions=PluginPermissions(network=True),
        )
    with pytest.raises(ValidationError):
        StrategyPluginManifest(
            strategy_id="noop",
            strategy_version="1.0.0",
            sdk_schema_version="1.0.0",
            runtime_protocol_version="1.0.0",
            feature_schema_version="1.0.0",
            config_schema_version="1.0.0",
            author="bergama",
            package_identity="pkg",
            capabilities={"supports_training": True, "supports_replay": True},
        )
    with pytest.raises(ValidationError):
        StrategyPluginManifest(
            strategy_id="noop",
            strategy_version="1.0.0",
            sdk_schema_version="1.0.0",
            runtime_protocol_version="1.0.0",
            feature_schema_version="1.0.0",
            config_schema_version="1.0.0",
            author="bergama",
            package_identity="pkg",
            capabilities={"supports_replay": True, "unknown_capability": True},
        )


def test_approved_capabilities_are_canonical_and_deterministic() -> None:
    left = StrategyPluginManifest(
        strategy_id="noop",
        strategy_version="1.0.0",
        sdk_schema_version="1.0.0",
        runtime_protocol_version="1.0.0",
        feature_schema_version="1.0.0",
        config_schema_version="1.0.0",
        author="bergama",
        package_identity="pkg",
        capabilities={"supports_batch": True, "supports_replay": True},
    )
    right = StrategyPluginManifest(
        strategy_id="noop",
        strategy_version="1.0.0",
        sdk_schema_version="1.0.0",
        runtime_protocol_version="1.0.0",
        feature_schema_version="1.0.0",
        config_schema_version="1.0.0",
        author="bergama",
        package_identity="pkg",
        capabilities={"supports_replay": True, "supports_batch": True},
    )
    assert left.capabilities == right.capabilities
    assert left.fingerprint() == right.fingerprint()


def test_deprecation_metadata_does_not_change_execution_fingerprint() -> None:
    before = sample_execution_context().execution_fingerprint
    _ = DeprecationDescriptor(
        symbol="old",
        deprecated_since="1.0.0",
        removal_not_before="2.0.0",
        replacement="new",
        migration_document="docs",
    )
    after = sample_execution_context().execution_fingerprint
    assert before == after


def test_evaluation_time_requires_exact_utc() -> None:
    base = sample_execution_context()
    payload = base.model_dump(mode="python")
    StrategyExecutionContext.model_validate(
        {**payload, "evaluation_time": datetime(2026, 7, 15, 14, 30, tzinfo=UTC)}
    )
    with pytest.raises(ValidationError):
        StrategyExecutionContext.model_validate(
            {**payload, "evaluation_time": datetime(2026, 7, 15, 14, 30)}
        )
    with pytest.raises(ValidationError):
        StrategyExecutionContext.model_validate(
            {
                **payload,
                "evaluation_time": datetime(
                    2026, 7, 15, 14, 30, tzinfo=timezone(timedelta(hours=1))
                ),
            }
        )
    with pytest.raises(ValidationError):
        StrategyExecutionContext.model_validate(
            {
                **payload,
                "evaluation_time": datetime(
                    2026, 7, 15, 14, 30, tzinfo=timezone(timedelta(hours=-5))
                ),
            }
        )
