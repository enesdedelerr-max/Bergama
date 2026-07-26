"""Integration: Feature Platform resolution into evaluate_batch (#67)."""

from __future__ import annotations

import pytest
from app.core.feature_platform_settings import FeaturePlatformSettings
from app.features.catalog import BAR_OHLCV_FEATURE_IDS
from app.market_data.keys import build_deduplication_key, build_idempotency_key
from app.strategy.models import QualitySummary, StrategyInput
from app.strategy.ports import InMemoryStrategyDecisionPort
from app.strategy.sdk_runtime.bar_feature_registry import build_bar_feature_schema_registry
from app.strategy.sdk_runtime.budgets import ExecutionBudgets
from app.strategy.sdk_runtime.engine import build_strategy_sdk_runtime_engine
from app.strategy.sdk_runtime.feature_assembler import FeatureAssembler
from app.strategy.sdk_runtime.feature_resolution import (
    resolve_feature_snapshot_for_strategy_input,
)
from app.strategy.sdk_runtime.reference import SdkNoOpStrategy
from app.strategy.sdk_runtime.registry import StrategySdkPluginRegistry
from bergama_strategy_sdk.compatibility import RuntimeCompatibilityPolicy
from bergama_strategy_sdk.config import StrategyConfig
from bergama_strategy_sdk.manifest import StrategyPluginManifest
from bergama_strategy_sdk.permissions import PluginPermissions
from tests.support.market_data_fixtures import make_bar
from tests.support.strategy_helpers import quality_assessment
from tests.support.strategy_sdk_helpers import execution_context_for_binding


def _bar_manifest() -> StrategyPluginManifest:
    return StrategyPluginManifest(
        strategy_id="bar-noop",
        strategy_version="1.0.0",
        sdk_schema_version="1.0.0",
        runtime_protocol_version="1.0.0",
        feature_schema_version="1.0.0",
        config_schema_version="1.0.0",
        author="bergama",
        package_identity="bergama.reference.bar_noop",
        required_features=BAR_OHLCV_FEATURE_IDS,
        permissions=PluginPermissions.empty(),
        capabilities={"supports_replay": True},
    )


@pytest.mark.asyncio
async def test_enabled_feature_platform_snapshot_feeds_evaluate_batch() -> None:
    bar = make_bar()
    assessment = quality_assessment(bar)
    strategy_input = StrategyInput(
        event=bar,
        instrument_id=bar.instrument,
        run_id="run-fp-1",
        session_id="session-fp-1",
        idempotency_key=build_idempotency_key(bar),
        deduplication_key=build_deduplication_key(bar),
        quality_summary=QualitySummary.from_event_and_assessment(event=bar, assessment=assessment),
        received_at=bar.ingested_at,
    )
    registry = build_bar_feature_schema_registry()
    assembler = FeatureAssembler(registry=registry, feature_schema_version="1.0.0")
    snapshot = resolve_feature_snapshot_for_strategy_input(
        strategy_input,
        feature_platform=FeaturePlatformSettings(enabled=True),
        assembler=assembler,
        required_features=BAR_OHLCV_FEATURE_IDS,
    )
    registry.validate_snapshot(snapshot, manifest=_bar_manifest())

    plugin_registry = StrategySdkPluginRegistry()
    manifest = _bar_manifest()
    plugin_registry.register(manifest, lambda _m: SdkNoOpStrategy())
    engine = build_strategy_sdk_runtime_engine(
        registry=plugin_registry,
        feature_registry=registry,
        compatibility_policy=RuntimeCompatibilityPolicy(
            sdk_schema_version="1.0.0",
            runtime_protocol_version="1.0.0",
            feature_schema_version="1.0.0",
            config_schema_version="1.0.0",
            allow_experimental=False,
        ),
        decision_port=InMemoryStrategyDecisionPort(),
        budgets=ExecutionBudgets(),
    )
    session = engine.create_session(
        run_id="run-fp-1",
        session_id="session-fp-1",
        plugins=((manifest, StrategyConfig(config_schema_version="1.0.0"), "bar:aapl:primary"),),
    )
    result = await session.evaluate_batch(
        feature_snapshot=snapshot,
        instrument_id=bar.instrument,
        contexts={
            "bar-noop": execution_context_for_binding(session.bindings[0], snapshot=snapshot)
        },
    )
    assert result.execution_summary.completed is True
    assert result.execution_summary.failed == 0
    assert len(result.decisions) == 1
