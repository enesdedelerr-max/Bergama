"""Runtime audit extensions (#406)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol, TypeVar

T = TypeVar("T")

LifecycleAuditEvent = Literal[
    "REPLACEMENT_REQUESTED",
    "COMPATIBILITY_VALIDATED",
    "NEW_INSTANCE_CREATED",
    "INITIALIZING",
    "INITIALIZED",
    "CUTOVER_STARTED",
    "CUTOVER_COMPLETED",
    "OLD_INSTANCE_DRAINING",
    "OLD_INSTANCE_DISPOSING",
    "OLD_INSTANCE_DISPOSED",
    "REPLACEMENT_COMPLETED",
    "FAILED",
    "DISABLED",
    "INCOMPATIBLE",
    "DISPOSED",
    "REPLACE_CANCELLED",
    "REPLACE_REJECTED",
]


@dataclass(frozen=True, slots=True)
class StrategyPluginFailureAudit:
    strategy_id: str
    strategy_version: str
    strategy_instance_id: str
    run_id: str
    session_id: str
    execution_id: str | None
    failure_code: str
    failure_type: str
    evaluation_time: datetime
    correlation_id: str | None
    causation_id: str | None


@dataclass(frozen=True, slots=True)
class StrategyLifecycleAudit:
    strategy_id: str
    strategy_version: str
    strategy_instance_id: str
    event: LifecycleAuditEvent


class StrategySdkAuditSink(Protocol):
    def record_plugin_failure(self, entry: StrategyPluginFailureAudit) -> None: ...

    def record_lifecycle(self, entry: StrategyLifecycleAudit) -> None: ...

    def clear(self) -> None: ...


class InMemoryStrategySdkAuditSink:
    def __init__(self, *, max_records: int = 10_000) -> None:
        self._max_records = max_records
        self.plugin_failures: list[StrategyPluginFailureAudit] = []
        self.lifecycle_events: list[StrategyLifecycleAudit] = []

    def record_plugin_failure(self, entry: StrategyPluginFailureAudit) -> None:
        self.plugin_failures.append(entry)
        self._trim(self.plugin_failures)

    def record_lifecycle(self, entry: StrategyLifecycleAudit) -> None:
        self.lifecycle_events.append(entry)
        self._trim(self.lifecycle_events)

    def clear(self) -> None:
        self.plugin_failures.clear()
        self.lifecycle_events.clear()

    def _trim(self, items: list[T]) -> None:
        overflow = len(items) - self._max_records
        if overflow > 0:
            del items[0:overflow]
