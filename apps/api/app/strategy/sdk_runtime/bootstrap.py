"""Bootstrap helpers for #406 SDK runtime tests and reference wiring."""

from __future__ import annotations

from bergama_strategy_sdk.compatibility import RuntimeCompatibilityPolicy
from bergama_strategy_sdk.config import StrategyConfig
from bergama_strategy_sdk.manifest import StrategyPluginManifest
from bergama_strategy_sdk.permissions import PluginPermissions

from app.strategy.sdk_runtime.feature_registry import FeatureSchemaDefinition, FeatureSchemaRegistry
from app.strategy.sdk_runtime.reference import SdkNoOpStrategy
from app.strategy.sdk_runtime.registry import StrategySdkPluginRegistry


def reference_plugin_manifest() -> StrategyPluginManifest:
    return StrategyPluginManifest(
        strategy_id="noop",
        strategy_version="1.0.0",
        sdk_schema_version="1.0.0",
        runtime_protocol_version="1.0.0",
        feature_schema_version="1.0.0",
        config_schema_version="1.0.0",
        author="bergama",
        package_identity="bergama.reference.noop",
        required_features=("EMA20", "EMA50"),
        permissions=PluginPermissions.empty(),
        capabilities={"supports_replay": True, "supports_incremental": True},
    )


def build_reference_feature_registry() -> FeatureSchemaRegistry:
    registry = FeatureSchemaRegistry()
    for feature_id in ("EMA20", "EMA50", "VWAP", "ATR", "VolumeProfile"):
        registry.register(
            FeatureSchemaDefinition(
                schema_id="technical",
                schema_version="1.0.0",
                feature_id=feature_id,
            )
        )
    return registry


def build_reference_plugin_registry() -> StrategySdkPluginRegistry:
    registry = StrategySdkPluginRegistry()
    manifest = reference_plugin_manifest()
    registry.register(manifest, lambda _manifest: SdkNoOpStrategy())
    return registry


def reference_runtime_policy() -> RuntimeCompatibilityPolicy:
    return RuntimeCompatibilityPolicy(
        sdk_schema_version="1.0.0",
        runtime_protocol_version="1.0.0",
        feature_schema_version="1.0.0",
        config_schema_version="1.0.0",
        allow_experimental=False,
    )


def reference_strategy_config() -> StrategyConfig:
    return StrategyConfig(
        config_schema_version="1.0.0",
        safe_metadata={"purpose": "reference"},
    )
