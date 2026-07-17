"""Plugin lifecycle orchestration (#406)."""

from __future__ import annotations

from dataclasses import dataclass, field

from bergama_strategy_sdk.compatibility import (
    RuntimeCompatibilityPolicy,
    validate_manifest_compatibility,
)
from bergama_strategy_sdk.errors import (
    StrategyBudgetExceededError,
    StrategyCompatibilityError,
    StrategyFeatureSchemaError,
    StrategyLifecycleError,
)
from bergama_strategy_sdk.execution import Strategy
from bergama_strategy_sdk.manifest import StrategyPluginManifest

from app.strategy.sdk_runtime.budgets import ExecutionBudgets
from app.strategy.sdk_runtime.feature_registry import FeatureSchemaRegistry
from app.strategy.sdk_runtime.health import PluginHealth, transition_health


@dataclass(slots=True)
class PluginLifecycle:
    manifest: StrategyPluginManifest
    strategy: Strategy | None = None
    health: PluginHealth = PluginHealth.CREATED
    _disposed: bool = field(default=False, init=False, repr=False)

    def initialize(
        self,
        *,
        strategy: Strategy,
        registry: FeatureSchemaRegistry,
        policy: RuntimeCompatibilityPolicy,
        budgets: ExecutionBudgets,
    ) -> None:
        if self.health not in {PluginHealth.CREATED, PluginHealth.DISABLED}:
            raise StrategyLifecycleError(detail=f"initialize_from_{self.health.value}")
        try:
            validate_manifest_compatibility(self.manifest, policy=policy)
            registry.validate_required_features(self.manifest.required_features)
            budgets.validate_manifest(self.manifest)
        except (
            StrategyCompatibilityError,
            StrategyFeatureSchemaError,
            StrategyBudgetExceededError,
        ):
            self.health = PluginHealth.INCOMPATIBLE
            raise
        self.health = transition_health(self.health, PluginHealth.INITIALIZING)
        self.strategy = strategy
        self.health = transition_health(self.health, PluginHealth.READY)

    def mark_failed_and_disabled(self) -> None:
        if self.health is PluginHealth.READY:
            self.health = transition_health(self.health, PluginHealth.FAILED)
        if self.health is PluginHealth.FAILED:
            self.health = transition_health(self.health, PluginHealth.DISABLED)

    def dispose(self) -> None:
        if self._disposed:
            return
        if self.health is PluginHealth.INCOMPATIBLE:
            self.health = transition_health(self.health, PluginHealth.DISPOSED)
            self._disposed = True
            self.strategy = None
            return
        if self.health in {PluginHealth.READY, PluginHealth.FAILED, PluginHealth.DISABLED}:
            self.health = transition_health(self.health, PluginHealth.DISPOSING)
        if self.health is PluginHealth.DISPOSING:
            self.health = transition_health(self.health, PluginHealth.DISPOSED)
            self._disposed = True
            self.strategy = None

    def mark_failed_from_initializing(self) -> None:
        if self.health is PluginHealth.INITIALIZING:
            self.health = transition_health(self.health, PluginHealth.FAILED)
        if self.health is PluginHealth.FAILED:
            self.health = transition_health(self.health, PluginHealth.DISABLED)
