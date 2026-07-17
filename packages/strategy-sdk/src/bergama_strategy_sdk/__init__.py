"""Bergama Strategy SDK — stable public author-facing API."""

from bergama_strategy_sdk.compatibility import (
    RuntimeCompatibilityPolicy,
    validate_manifest_compatibility,
)
from bergama_strategy_sdk.config import StrategyConfig
from bergama_strategy_sdk.context import StrategyExecutionContext
from bergama_strategy_sdk.decisions import StrategyAction, StrategyDecision, StrategyReasonCode
from bergama_strategy_sdk.deprecation import DeprecationDescriptor, MigrationGuidance
from bergama_strategy_sdk.errors import (
    StrategyBudgetExceededError,
    StrategyCompatibilityError,
    StrategyConfigurationError,
    StrategyContractViolation,
    StrategyExecutionError,
    StrategyFeatureSchemaError,
    StrategyLifecycleError,
    StrategyManifestError,
    StrategyPermissionError,
    StrategyPluginCrash,
    StrategySdkError,
    StrategyStateError,
    StrategyTimeoutError,
    StrategyValidationError,
)
from bergama_strategy_sdk.execution import Strategy, StrategyExecutionOutput
from bergama_strategy_sdk.features import FeatureSnapshot, FeatureValue
from bergama_strategy_sdk.fingerprints import (
    build_decision_id,
    configuration_fingerprint,
    execution_fingerprint,
    feature_fingerprint,
    state_fingerprint,
    strategy_fingerprint,
)
from bergama_strategy_sdk.manifest import PluginCapability, StrategyPluginManifest
from bergama_strategy_sdk.permissions import PluginPermissions
from bergama_strategy_sdk.state import NextStrategyState, PreviousStrategyState
from bergama_strategy_sdk.versions import VersionAxes

__all__ = [
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
]

PUBLIC_API_VERSION = "1.0.0"
