"""#406 SDK runtime session with recovery and batch orchestration."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Literal

from bergama_strategy_sdk.compatibility import RuntimeCompatibilityPolicy
from bergama_strategy_sdk.config import StrategyConfig
from bergama_strategy_sdk.context import StrategyExecutionContext
from bergama_strategy_sdk.decisions import StrategyDecision
from bergama_strategy_sdk.errors import (
    StrategyBudgetExceededError,
    StrategyCompatibilityError,
    StrategyContractViolation,
    StrategyExecutionError,
    StrategyFeatureSchemaError,
    StrategyLifecycleError,
    StrategyPluginCrash,
    StrategyStateError,
    StrategyTimeoutError,
)
from bergama_strategy_sdk.execution import Strategy, StrategyExecutionOutput
from bergama_strategy_sdk.features import FeatureSnapshot
from bergama_strategy_sdk.fingerprints import configuration_fingerprint, strategy_fingerprint
from bergama_strategy_sdk.manifest import StrategyPluginManifest
from bergama_strategy_sdk.state import PreviousStrategyState

from app.market_data.identity import InstrumentId
from app.strategy.errors import StrategyClosedError, StrategyDownstreamPublishError
from app.strategy.ports import StrategyDecisionPort
from app.strategy.sdk_runtime.audit import (
    InMemoryStrategySdkAuditSink,
    LifecycleAuditEvent,
    StrategyLifecycleAudit,
    StrategyPluginFailureAudit,
)
from app.strategy.sdk_runtime.batch_result import (
    ExecutionSummary,
    PluginFailure,
    PluginStateCommit,
    SkippedPlugin,
    StrategyBatchExecutionResult,
)
from app.strategy.sdk_runtime.budgets import ExecutionBudgets
from app.strategy.sdk_runtime.feature_registry import FeatureSchemaRegistry
from app.strategy.sdk_runtime.health import PluginHealth
from app.strategy.sdk_runtime.lifecycle import PluginLifecycle
from app.strategy.sdk_runtime.metrics import StrategySdkRuntimeMetrics
from app.strategy.sdk_runtime.registry import StrategySdkPluginRegistry
from app.strategy.sdk_runtime.sdk_decision_adapter import sdk_decision_to_legacy
from app.strategy.sdk_runtime.state_contract import validate_next_state, validate_previous_state


@dataclass(frozen=True, slots=True)
class BindingIdentity:
    """Immutable identity captured from a leased binding."""

    strategy_id: str
    strategy_version: str
    strategy_instance_id: str
    manifest_fingerprint: str
    strategy_fingerprint: str
    runtime_protocol_version: str
    feature_schema_version: str
    config_schema_version: str
    configuration_fingerprint: str
    sdk_schema_version: str


@dataclass(slots=True)
class SdkRuntimeBinding:
    lifecycle: PluginLifecycle
    config: StrategyConfig
    strategy_instance_id: str
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    leases: int = 0
    lease_idle: asyncio.Event = field(default_factory=asyncio.Event)

    def __post_init__(self) -> None:
        self.lease_idle.set()

    def identity(self) -> BindingIdentity:
        manifest = self.lifecycle.manifest
        return BindingIdentity(
            strategy_id=manifest.strategy_id,
            strategy_version=manifest.strategy_version,
            strategy_instance_id=self.strategy_instance_id,
            manifest_fingerprint=manifest.fingerprint(),
            strategy_fingerprint=strategy_fingerprint(
                strategy_id=manifest.strategy_id,
                strategy_version=manifest.strategy_version,
                strategy_instance_id=self.strategy_instance_id,
                sdk_schema_version=manifest.sdk_schema_version,
            ),
            runtime_protocol_version=manifest.runtime_protocol_version,
            feature_schema_version=manifest.feature_schema_version,
            config_schema_version=manifest.config_schema_version,
            configuration_fingerprint=configuration_fingerprint(self.config.fingerprint_payload()),
            sdk_schema_version=manifest.sdk_schema_version,
        )


@dataclass(slots=True)
class StrategySdkRuntimeSession:
    run_id: str
    session_id: str
    bindings: list[SdkRuntimeBinding]
    decision_port: StrategyDecisionPort | None
    feature_registry: FeatureSchemaRegistry
    compatibility_policy: RuntimeCompatibilityPolicy
    registry: StrategySdkPluginRegistry
    budgets: ExecutionBudgets = field(default_factory=ExecutionBudgets)
    audit_sink: InMemoryStrategySdkAuditSink = field(default_factory=InMemoryStrategySdkAuditSink)
    metrics: StrategySdkRuntimeMetrics = field(default_factory=StrategySdkRuntimeMetrics)
    _closed: bool = field(default=False, init=False, repr=False)
    _routing_locks: dict[str, asyncio.Lock] = field(
        default_factory=lambda: defaultdict(asyncio.Lock), init=False, repr=False
    )
    _replacement_cleanups: set[asyncio.Task[None]] = field(
        default_factory=set, init=False, repr=False
    )

    @property
    def closed(self) -> bool:
        return self._closed

    def binding_for(self, strategy_id: str) -> SdkRuntimeBinding | None:
        for binding in self.bindings:
            if binding.lifecycle.manifest.strategy_id == strategy_id:
                return binding
        return None

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._replacement_cleanups:
            await asyncio.gather(*tuple(self._replacement_cleanups), return_exceptions=True)
            self._replacement_cleanups.clear()
        for binding in self.bindings:
            binding.lifecycle.dispose()
            self.metrics.plugin_disposed_total += 1
        self.audit_sink.clear()
        self.metrics.clear()

    async def evaluate_batch(
        self,
        *,
        feature_snapshot: FeatureSnapshot,
        instrument_id: InstrumentId,
        contexts: dict[str, StrategyExecutionContext],
        previous_states: dict[str, PreviousStrategyState | None] | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> StrategyBatchExecutionResult:
        if self._closed:
            raise StrategyClosedError()
        if instrument_id.instrument_key != feature_snapshot.instrument_key:
            raise StrategyContractViolation(detail="instrument_key_mismatch")
        self.budgets.validate_feature_snapshot(feature_snapshot)
        decisions: list[StrategyDecision] = []
        failures: list[PluginFailure] = []
        skipped: list[SkippedPlugin] = []
        state_commits: list[PluginStateCommit] = []
        published_decision_ids: list[str] = []
        resolved_states = previous_states or {}
        # Deterministic plugin order for this batch; live binding resolved per plugin.
        order = [binding.lifecycle.manifest.strategy_id for binding in list(self.bindings)]
        for strategy_id in order:
            context = contexts.get(strategy_id)
            if context is None:
                raise StrategyExecutionError(detail=f"missing_context:{strategy_id}")
            leased = await self._acquire_ready_lease(strategy_id)
            if leased is None:
                binding = self.binding_for(strategy_id)
                if binding is None:
                    continue
                skipped.append(
                    SkippedPlugin(
                        strategy_id=strategy_id,
                        strategy_version=binding.lifecycle.manifest.strategy_version,
                        strategy_instance_id=binding.strategy_instance_id,
                        reason=_skip_reason(binding.lifecycle.health),
                        plugin_health=binding.lifecycle.health,
                    )
                )
                self.metrics.skipped_plugin_total += 1
                continue
            binding = leased
            try:
                self._validate_feature_snapshot_for_binding(
                    feature_snapshot=feature_snapshot,
                    binding=binding,
                )
                leased_identity = binding.identity()
                self._validate_context_against_identity(
                    context=context,
                    identity=leased_identity,
                )
                output = await self._execute_binding(
                    binding=binding,
                    feature_snapshot=feature_snapshot,
                    context=context,
                    previous_state=resolved_states.get(strategy_id),
                )
            except asyncio.CancelledError:
                self.metrics.cancellation_total += 1
                raise
            except StrategyDownstreamPublishError:
                self.metrics.downstream_failure_total += 1
                raise
            except StrategyFeatureSchemaError as exc:
                self.metrics.feature_schema_rejection_total += 1
                raise StrategyFeatureSchemaError(detail=exc.detail) from exc
            except StrategyContractViolation as exc:
                if (exc.detail or "").startswith("binding_context_mismatch:"):
                    self.metrics.contract_violation_total += 1
                    raise
                self._handle_plugin_failure(
                    binding=binding,
                    context=context,
                    exc=exc,
                    failure_code=exc.code,
                    failures=failures,
                )
                self._enforce_failure_budget(failures)
                continue
            except StrategyBudgetExceededError as exc:
                if exc.detail == "plugin_failures_per_batch":
                    raise
                self._handle_plugin_failure(
                    binding=binding,
                    context=context,
                    exc=exc,
                    failure_code=exc.code,
                    failures=failures,
                )
                self._enforce_failure_budget(failures)
                continue
            except (
                StrategyTimeoutError,
                StrategyStateError,
                StrategyPluginCrash,
                StrategyExecutionError,
                StrategyLifecycleError,
            ) as exc:
                self._handle_plugin_failure(
                    binding=binding,
                    context=context,
                    exc=exc,
                    failure_code=exc.code,
                    failures=failures,
                )
                self._enforce_failure_budget(failures)
                continue
            except Exception as exc:
                wrapped = StrategyPluginCrash(detail=type(exc).__name__)
                self._handle_plugin_failure(
                    binding=binding,
                    context=context,
                    exc=wrapped,
                    failure_code=wrapped.code,
                    failures=failures,
                )
                self._enforce_failure_budget(failures)
                continue
            finally:
                await self._release_lease(binding)

            self.metrics.execution_success_total += 1
            if output.next_state is not None:
                state_commits.append(
                    PluginStateCommit(
                        strategy_id=context.strategy_id,
                        strategy_version=context.strategy_version,
                        strategy_instance_id=context.strategy_instance_id,
                        next_state=output.next_state,
                    )
                )
            if self.decision_port is not None:
                try:
                    await self.decision_port.publish_decision(
                        sdk_decision_to_legacy(
                            output.decision,
                            instrument_id=instrument_id,
                            quality_summary=None,
                        )
                    )
                except StrategyDownstreamPublishError:
                    self.metrics.downstream_failure_total += 1
                    raise
                except Exception as exc:
                    self.metrics.downstream_failure_total += 1
                    raise StrategyDownstreamPublishError(
                        detail=type(exc).__name__,
                        published_decision_ids=tuple(published_decision_ids),
                        failed_decision_id=output.decision.decision_id,
                        strategy_id=context.strategy_id,
                        strategy_version=context.strategy_version,
                        strategy_instance_id=context.strategy_instance_id,
                        correlation_id=context.correlation_id or correlation_id,
                        causation_id=context.causation_id or causation_id,
                    ) from exc
            published_decision_ids.append(output.decision.decision_id)
            decisions.append(output.decision)
        summary = ExecutionSummary(
            total=len(order),
            succeeded=len(decisions),
            failed=len(failures),
            skipped=len(skipped),
            completed=len(failures) == 0,
        )
        if failures and decisions:
            self.metrics.batch_partial_success_total += 1
        return StrategyBatchExecutionResult(
            decisions=tuple(decisions),
            plugin_failures=tuple(failures),
            skipped_plugins=tuple(skipped),
            execution_summary=summary,
            state_commits=tuple(state_commits),
        )

    async def replace_plugin(
        self,
        *,
        strategy_id: str,
        manifest: StrategyPluginManifest,
        config: StrategyConfig,
        strategy_instance_id: str,
    ) -> SdkRuntimeBinding:
        """Explicit versioned replacement via registry factory. Never auto-migrates."""
        if self._closed:
            raise StrategyClosedError()
        if manifest.strategy_id != strategy_id:
            raise StrategyLifecycleError(detail="replace_strategy_id_mismatch")
        old = self.binding_for(strategy_id)
        if old is None:
            raise StrategyLifecycleError(detail=f"replace_unknown_strategy:{strategy_id}")
        if old.lifecycle.health is not PluginHealth.READY:
            raise StrategyLifecycleError(detail=f"replace_from_{old.lifecycle.health.value}")

        self._audit_lifecycle(
            strategy_id=manifest.strategy_id,
            strategy_version=manifest.strategy_version,
            strategy_instance_id=strategy_instance_id,
            event="REPLACEMENT_REQUESTED",
        )
        new_lifecycle = PluginLifecycle(manifest=manifest)
        cutover_complete = False
        cleanup_task: asyncio.Task[None] | None = None
        try:
            self._audit_lifecycle(
                strategy_id=manifest.strategy_id,
                strategy_version=manifest.strategy_version,
                strategy_instance_id=strategy_instance_id,
                event="INITIALIZING",
            )
            strategy = self.registry.create(manifest)
            self._audit_lifecycle(
                strategy_id=manifest.strategy_id,
                strategy_version=manifest.strategy_version,
                strategy_instance_id=strategy_instance_id,
                event="NEW_INSTANCE_CREATED",
            )
            new_lifecycle.initialize(
                strategy=strategy,
                registry=self.feature_registry,
                policy=self.compatibility_policy,
                budgets=self.budgets,
            )
            self.budgets.validate_config(config)
            self._audit_lifecycle(
                strategy_id=manifest.strategy_id,
                strategy_version=manifest.strategy_version,
                strategy_instance_id=strategy_instance_id,
                event="COMPATIBILITY_VALIDATED",
            )
            new_binding = SdkRuntimeBinding(
                lifecycle=new_lifecycle,
                config=config,
                strategy_instance_id=strategy_instance_id,
            )
            self.metrics.plugin_initialized_total += 1
            self.metrics.plugin_ready_total += 1
            self._audit_lifecycle(
                strategy_id=manifest.strategy_id,
                strategy_version=manifest.strategy_version,
                strategy_instance_id=strategy_instance_id,
                event="INITIALIZED",
            )

            self._audit_lifecycle(
                strategy_id=manifest.strategy_id,
                strategy_version=manifest.strategy_version,
                strategy_instance_id=strategy_instance_id,
                event="CUTOVER_STARTED",
            )
            async with self._routing_locks[strategy_id]:
                index = self.bindings.index(old)
                self.bindings[index] = new_binding
                cutover_complete = True
            self._audit_lifecycle(
                strategy_id=manifest.strategy_id,
                strategy_version=manifest.strategy_version,
                strategy_instance_id=strategy_instance_id,
                event="CUTOVER_COMPLETED",
            )

            cleanup_task = asyncio.create_task(
                self._drain_and_dispose_old(
                    old=old,
                    new_manifest=manifest,
                    new_strategy_instance_id=strategy_instance_id,
                ),
                name=f"replace-cleanup:{strategy_id}",
            )
            self._replacement_cleanups.add(cleanup_task)
            cleanup_task.add_done_callback(self._replacement_cleanups.discard)
            await asyncio.shield(cleanup_task)
            return new_binding
        except asyncio.CancelledError:
            self.metrics.cancellation_total += 1
            self.metrics.plugin_replace_cancelled_total += 1
            if cutover_complete:
                self._audit_lifecycle(
                    strategy_id=manifest.strategy_id,
                    strategy_version=manifest.strategy_version,
                    strategy_instance_id=strategy_instance_id,
                    event="REPLACE_CANCELLED",
                )
            else:
                self._dispose_unrouted_lifecycle(
                    lifecycle=new_lifecycle,
                    strategy_id=manifest.strategy_id,
                    strategy_version=manifest.strategy_version,
                    strategy_instance_id=strategy_instance_id,
                    event="REPLACE_CANCELLED",
                )
            raise
        except (
            StrategyCompatibilityError,
            StrategyFeatureSchemaError,
            StrategyBudgetExceededError,
        ) as exc:
            self.metrics.compatibility_rejection_total += 1
            self.metrics.plugin_incompatible_total += 1
            self.metrics.plugin_replace_rejected_total += 1
            if "experimental" in (exc.detail or ""):
                self.metrics.experimental_rejection_total += 1
            self.audit_sink.record_lifecycle(
                StrategyLifecycleAudit(
                    strategy_id=manifest.strategy_id,
                    strategy_version=manifest.strategy_version,
                    strategy_instance_id=strategy_instance_id,
                    event="INCOMPATIBLE",
                )
            )
            self._dispose_unrouted_lifecycle(
                lifecycle=new_lifecycle,
                strategy_id=manifest.strategy_id,
                strategy_version=manifest.strategy_version,
                strategy_instance_id=strategy_instance_id,
                event="REPLACE_REJECTED",
            )
            raise
        except Exception:
            self.metrics.plugin_replace_rejected_total += 1
            if new_lifecycle.health is PluginHealth.CREATED:
                new_lifecycle.health = PluginHealth.INITIALIZING
            if new_lifecycle.health is PluginHealth.INITIALIZING:
                new_lifecycle.mark_failed_from_initializing()
            elif new_lifecycle.health is PluginHealth.READY:
                new_lifecycle.mark_failed_and_disabled()
            self._dispose_unrouted_lifecycle(
                lifecycle=new_lifecycle,
                strategy_id=manifest.strategy_id,
                strategy_version=manifest.strategy_version,
                strategy_instance_id=strategy_instance_id,
                event="REPLACE_REJECTED",
            )
            raise

    def register_factory_for_tests(
        self,
        *,
        manifest: StrategyPluginManifest,
        strategy: Strategy,
    ) -> None:
        """Test-only helper to register a factory closing over a concrete instance."""
        self.registry.register(manifest, lambda _manifest: strategy)

    def _enforce_failure_budget(self, failures: list[PluginFailure]) -> None:
        try:
            self.budgets.validate_failure_count(len(failures))
        except StrategyBudgetExceededError:
            self.metrics.budget_violation_total += 1
            raise

    def _validate_feature_snapshot_for_binding(
        self,
        *,
        feature_snapshot: FeatureSnapshot,
        binding: SdkRuntimeBinding,
    ) -> None:
        self.feature_registry.validate_snapshot(
            feature_snapshot,
            manifest=binding.lifecycle.manifest,
        )

    def _validate_context_against_identity(
        self,
        *,
        context: StrategyExecutionContext,
        identity: BindingIdentity,
    ) -> None:
        checks = (
            ("strategy_id", context.strategy_id, identity.strategy_id),
            ("strategy_version", context.strategy_version, identity.strategy_version),
            (
                "strategy_instance_id",
                context.strategy_instance_id,
                identity.strategy_instance_id,
            ),
            (
                "runtime_protocol_version",
                context.runtime_protocol_version,
                identity.runtime_protocol_version,
            ),
            (
                "feature_schema_version",
                context.feature_schema_version,
                identity.feature_schema_version,
            ),
            (
                "config_schema_version",
                context.config_schema_version,
                identity.config_schema_version,
            ),
            (
                "strategy_fingerprint",
                context.strategy_fingerprint,
                identity.strategy_fingerprint,
            ),
            (
                "configuration_fingerprint",
                context.configuration_fingerprint,
                identity.configuration_fingerprint,
            ),
            ("sdk_schema_version", context.sdk_schema_version, identity.sdk_schema_version),
        )
        for axis, actual, expected in checks:
            if actual != expected:
                raise StrategyContractViolation(detail=f"binding_context_mismatch:{axis}")

    async def _drain_and_dispose_old(
        self,
        *,
        old: SdkRuntimeBinding,
        new_manifest: StrategyPluginManifest,
        new_strategy_instance_id: str,
    ) -> None:
        self._audit_lifecycle(
            strategy_id=old.lifecycle.manifest.strategy_id,
            strategy_version=old.lifecycle.manifest.strategy_version,
            strategy_instance_id=old.strategy_instance_id,
            event="OLD_INSTANCE_DRAINING",
        )
        while old.leases > 0:
            await old.lease_idle.wait()
        self._audit_lifecycle(
            strategy_id=old.lifecycle.manifest.strategy_id,
            strategy_version=old.lifecycle.manifest.strategy_version,
            strategy_instance_id=old.strategy_instance_id,
            event="OLD_INSTANCE_DISPOSING",
        )
        async with old.lock:
            if old.lifecycle.health is not PluginHealth.DISPOSED:
                old.lifecycle.dispose()
        self.metrics.plugin_disposed_total += 1
        self.metrics.plugin_replaced_total += 1
        self._audit_lifecycle(
            strategy_id=old.lifecycle.manifest.strategy_id,
            strategy_version=old.lifecycle.manifest.strategy_version,
            strategy_instance_id=old.strategy_instance_id,
            event="OLD_INSTANCE_DISPOSED",
        )
        self._audit_lifecycle(
            strategy_id=new_manifest.strategy_id,
            strategy_version=new_manifest.strategy_version,
            strategy_instance_id=new_strategy_instance_id,
            event="REPLACEMENT_COMPLETED",
        )

    async def _acquire_ready_lease(self, strategy_id: str) -> SdkRuntimeBinding | None:
        async with self._routing_locks[strategy_id]:
            binding = self.binding_for(strategy_id)
            if binding is None or binding.lifecycle.health is not PluginHealth.READY:
                return None
            binding.leases += 1
            binding.lease_idle.clear()
            return binding

    async def _release_lease(self, binding: SdkRuntimeBinding) -> None:
        strategy_id = binding.lifecycle.manifest.strategy_id
        async with self._routing_locks[strategy_id]:
            binding.leases = max(0, binding.leases - 1)
            if binding.leases == 0:
                binding.lease_idle.set()

    async def _execute_binding(
        self,
        *,
        binding: SdkRuntimeBinding,
        feature_snapshot: FeatureSnapshot,
        context: StrategyExecutionContext,
        previous_state: PreviousStrategyState | None,
    ) -> StrategyExecutionOutput:
        async with binding.lock:
            if binding.lifecycle.health is not PluginHealth.READY:
                raise StrategyLifecycleError(
                    detail=f"execute_from_{binding.lifecycle.health.value}"
                )
            strategy = binding.lifecycle.strategy
            if strategy is None:
                raise StrategyExecutionError(detail="strategy_not_initialized")
            self.budgets.validate_config(binding.config)
            validate_previous_state(
                previous_state,
                strategy_id=context.strategy_id,
                strategy_instance_id=context.strategy_instance_id,
            )
            if previous_state is not None:
                self.budgets.validate_state(previous_state)
            try:
                output = await asyncio.wait_for(
                    strategy.execute(
                        previous_state=previous_state,
                        feature_snapshot=feature_snapshot,
                        context=context,
                        config=binding.config,
                    ),
                    timeout=self.budgets.execution_timeout_ms / 1000.0,
                )
            except TimeoutError as exc:
                raise StrategyTimeoutError(detail="execution_timeout") from exc
            self.budgets.validate_output(output)
            validated_next = validate_next_state(
                output,
                previous_state=previous_state,
                strategy_id=context.strategy_id,
                strategy_instance_id=context.strategy_instance_id,
            )
            if validated_next is not output.next_state:
                return StrategyExecutionOutput(decision=output.decision, next_state=validated_next)
            return output

    def _dispose_unrouted_lifecycle(
        self,
        *,
        lifecycle: PluginLifecycle,
        strategy_id: str,
        strategy_version: str,
        strategy_instance_id: str,
        event: Literal["REPLACE_CANCELLED", "REPLACE_REJECTED"],
    ) -> None:
        if lifecycle.health not in {PluginHealth.DISPOSED, PluginHealth.DISPOSING}:
            if lifecycle.health in {
                PluginHealth.READY,
                PluginHealth.INCOMPATIBLE,
                PluginHealth.DISABLED,
                PluginHealth.FAILED,
            }:
                lifecycle.dispose()
            elif lifecycle.health in {PluginHealth.CREATED, PluginHealth.INITIALIZING}:
                if lifecycle.health is PluginHealth.CREATED:
                    lifecycle.health = PluginHealth.INITIALIZING
                lifecycle.mark_failed_from_initializing()
                lifecycle.dispose()
            self.metrics.plugin_disposed_total += 1
        self.audit_sink.record_lifecycle(
            StrategyLifecycleAudit(
                strategy_id=strategy_id,
                strategy_version=strategy_version,
                strategy_instance_id=strategy_instance_id,
                event=event,
            )
        )

    def _audit_lifecycle(
        self,
        *,
        strategy_id: str,
        strategy_version: str,
        strategy_instance_id: str,
        event: LifecycleAuditEvent,
    ) -> None:
        self.audit_sink.record_lifecycle(
            StrategyLifecycleAudit(
                strategy_id=strategy_id,
                strategy_version=strategy_version,
                strategy_instance_id=strategy_instance_id,
                event=event,
            )
        )

    def _handle_plugin_failure(
        self,
        *,
        binding: SdkRuntimeBinding,
        context: StrategyExecutionContext,
        exc: Exception,
        failure_code: str,
        failures: list[PluginFailure],
    ) -> None:
        binding.lifecycle.mark_failed_and_disabled()
        self.metrics.plugin_failed_total += 1
        self.metrics.plugin_disabled_total += 1
        if isinstance(exc, StrategyPluginCrash):
            self.metrics.plugin_crash_total += 1
        if isinstance(exc, StrategyContractViolation):
            self.metrics.contract_violation_total += 1
        if isinstance(exc, StrategyTimeoutError):
            self.metrics.execution_timeout_total += 1
        if isinstance(exc, StrategyBudgetExceededError):
            self.metrics.budget_violation_total += 1
        if isinstance(exc, StrategyStateError):
            self.metrics.state_error_total += 1
        safe_metadata: dict[str, str] = {}
        self.budgets.validate_failure_metadata(safe_metadata)
        failure = PluginFailure(
            strategy_id=context.strategy_id,
            strategy_version=context.strategy_version,
            strategy_instance_id=context.strategy_instance_id,
            run_id=context.run_id,
            session_id=context.session_id,
            execution_id=context.execution_id,
            correlation_id=context.correlation_id,
            causation_id=context.causation_id,
            evaluation_time=context.evaluation_time,
            failure_code=failure_code,
            failure_type=type(exc).__name__,
            plugin_health=binding.lifecycle.health,
            safe_metadata=safe_metadata,
        )
        failures.append(failure)
        self.audit_sink.record_plugin_failure(
            StrategyPluginFailureAudit(
                strategy_id=failure.strategy_id,
                strategy_version=failure.strategy_version,
                strategy_instance_id=failure.strategy_instance_id,
                run_id=failure.run_id,
                session_id=failure.session_id,
                execution_id=failure.execution_id,
                failure_code=failure.failure_code,
                failure_type=failure.failure_type,
                evaluation_time=failure.evaluation_time,
                correlation_id=failure.correlation_id,
                causation_id=failure.causation_id,
            )
        )
        self.audit_sink.record_lifecycle(
            StrategyLifecycleAudit(
                strategy_id=failure.strategy_id,
                strategy_version=failure.strategy_version,
                strategy_instance_id=failure.strategy_instance_id,
                event="FAILED",
            )
        )
        self.audit_sink.record_lifecycle(
            StrategyLifecycleAudit(
                strategy_id=failure.strategy_id,
                strategy_version=failure.strategy_version,
                strategy_instance_id=failure.strategy_instance_id,
                event="DISABLED",
            )
        )


def _skip_reason(
    health: PluginHealth,
) -> Literal["DISABLED", "INCOMPATIBLE", "DISPOSED", "NOT_READY"]:
    if health is PluginHealth.DISABLED:
        return "DISABLED"
    if health is PluginHealth.INCOMPATIBLE:
        return "INCOMPATIBLE"
    if health is PluginHealth.DISPOSED:
        return "DISPOSED"
    return "NOT_READY"
