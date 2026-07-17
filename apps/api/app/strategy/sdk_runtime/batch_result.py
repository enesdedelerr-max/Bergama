"""Structured runtime batch execution result (#406)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from bergama_strategy_sdk.decisions import StrategyDecision
from bergama_strategy_sdk.state import NextStrategyState

from app.strategy.sdk_runtime.health import PluginHealth


@dataclass(frozen=True, slots=True)
class PluginFailure:
    strategy_id: str
    strategy_version: str
    strategy_instance_id: str
    run_id: str
    session_id: str
    execution_id: str | None
    correlation_id: str | None
    causation_id: str | None
    evaluation_time: datetime
    failure_code: str
    failure_type: str
    plugin_health: PluginHealth
    safe_metadata: dict[str, str]


@dataclass(frozen=True, slots=True)
class SkippedPlugin:
    strategy_id: str
    strategy_version: str
    strategy_instance_id: str
    reason: Literal["DISABLED", "INCOMPATIBLE", "DISPOSED", "NOT_READY"]
    plugin_health: PluginHealth


@dataclass(frozen=True, slots=True)
class ExecutionSummary:
    total: int
    succeeded: int
    failed: int
    skipped: int
    completed: bool


@dataclass(frozen=True, slots=True)
class PluginStateCommit:
    """Runtime-owned validated next_state handoff — host owns persistence."""

    strategy_id: str
    strategy_version: str
    strategy_instance_id: str
    next_state: NextStrategyState


@dataclass(frozen=True, slots=True)
class StrategyBatchExecutionResult:
    decisions: tuple[StrategyDecision, ...]
    plugin_failures: tuple[PluginFailure, ...]
    skipped_plugins: tuple[SkippedPlugin, ...]
    execution_summary: ExecutionSummary
    state_commits: tuple[PluginStateCommit, ...] = ()
