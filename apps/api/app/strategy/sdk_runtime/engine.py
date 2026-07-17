"""#406 SDK runtime engine coordinator."""

from __future__ import annotations

from dataclasses import dataclass

from bergama_strategy_sdk.compatibility import RuntimeCompatibilityPolicy
from bergama_strategy_sdk.config import StrategyConfig
from bergama_strategy_sdk.manifest import StrategyPluginManifest

from app.strategy.errors import StrategyClosedError, StrategyConfigurationError
from app.strategy.ports import StrategyDecisionPort
from app.strategy.sdk_runtime.audit import InMemoryStrategySdkAuditSink
from app.strategy.sdk_runtime.budgets import ExecutionBudgets
from app.strategy.sdk_runtime.feature_registry import FeatureSchemaRegistry
from app.strategy.sdk_runtime.lifecycle import PluginLifecycle
from app.strategy.sdk_runtime.registry import StrategySdkPluginRegistry
from app.strategy.sdk_runtime.session import SdkRuntimeBinding, StrategySdkRuntimeSession


@dataclass(slots=True)
class StrategySdkRuntimeEngine:
    registry: StrategySdkPluginRegistry
    feature_registry: FeatureSchemaRegistry
    compatibility_policy: RuntimeCompatibilityPolicy
    decision_port: StrategyDecisionPort | None = None
    budgets: ExecutionBudgets | None = None
    audit_max_records: int = 10_000
    max_plugins_per_session: int = 16
    _closed: bool = False

    async def aclose(self) -> None:
        self._closed = True

    def create_session(
        self,
        *,
        run_id: str,
        session_id: str,
        plugins: tuple[tuple[StrategyPluginManifest, StrategyConfig, str], ...],
        decision_port: StrategyDecisionPort | None = None,
    ) -> StrategySdkRuntimeSession:
        if self._closed:
            raise StrategyClosedError()
        if len(plugins) > self.max_plugins_per_session:
            raise StrategyConfigurationError(detail="too_many_plugins")
        bindings: list[SdkRuntimeBinding] = []
        budgets = self.budgets if self.budgets is not None else ExecutionBudgets()
        for manifest, config, strategy_instance_id in plugins:
            lifecycle = PluginLifecycle(manifest=manifest)
            strategy = self.registry.create(manifest)
            lifecycle.initialize(
                strategy=strategy,
                registry=self.feature_registry,
                policy=self.compatibility_policy,
                budgets=budgets,
            )
            bindings.append(
                SdkRuntimeBinding(
                    lifecycle=lifecycle,
                    config=config,
                    strategy_instance_id=strategy_instance_id,
                )
            )
        session = StrategySdkRuntimeSession(
            run_id=run_id,
            session_id=session_id,
            bindings=bindings,
            decision_port=decision_port if decision_port is not None else self.decision_port,
            feature_registry=self.feature_registry,
            compatibility_policy=self.compatibility_policy,
            registry=self.registry,
            budgets=budgets,
            audit_sink=InMemoryStrategySdkAuditSink(max_records=self.audit_max_records),
        )
        for _binding in bindings:
            session.metrics.plugin_initialized_total += 1
            session.metrics.plugin_ready_total += 1
        return session


def build_strategy_sdk_runtime_engine(
    *,
    registry: StrategySdkPluginRegistry | None = None,
    feature_registry: FeatureSchemaRegistry | None = None,
    compatibility_policy: RuntimeCompatibilityPolicy | None = None,
    decision_port: StrategyDecisionPort | None = None,
    budgets: ExecutionBudgets | None = None,
    audit_max_records: int = 10_000,
    max_plugins_per_session: int = 16,
) -> StrategySdkRuntimeEngine:
    return StrategySdkRuntimeEngine(
        registry=registry if registry is not None else StrategySdkPluginRegistry(),
        feature_registry=(
            feature_registry if feature_registry is not None else FeatureSchemaRegistry()
        ),
        compatibility_policy=(
            compatibility_policy
            if compatibility_policy is not None
            else RuntimeCompatibilityPolicy()
        ),
        decision_port=decision_port,
        budgets=budgets,
        audit_max_records=audit_max_records,
        max_plugins_per_session=max_plugins_per_session,
    )
