"""Bounded process-local Strategy Engine metrics."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from app.strategy.models import StrategyAction, StrategyDecision, StrategyInput


@dataclass(slots=True)
class StrategyMetrics:
    """Counters owned by one StrategyEngine instance. No high-cardinality labels."""

    inputs_received_total: int = 0
    inputs_evaluated_total: int = 0
    inputs_accepted_total: int = 0
    inputs_degraded_total: int = 0
    inputs_rejected_total: int = 0
    decisions_emitted_total: int = 0
    no_action_decisions_total: int = 0
    strategy_errors_total: int = 0
    downstream_errors_total: int = 0
    processing_latency_ms_total: float = 0.0
    processing_latency_samples: int = 0
    decision_counts: Counter[str] = field(default_factory=Counter)

    def record_input(self, strategy_input: StrategyInput) -> None:
        self.inputs_received_total += 1
        if strategy_input.quality_summary.is_degraded:
            self.inputs_degraded_total += 1
        else:
            self.inputs_accepted_total += 1

    def record_rejected_input(self) -> None:
        self.inputs_rejected_total += 1

    def record_decision(self, decision: StrategyDecision) -> None:
        self.inputs_evaluated_total += 1
        self.decisions_emitted_total += 1
        self.decision_counts[decision.action.value] += 1
        if decision.action is StrategyAction.NO_ACTION:
            self.no_action_decisions_total += 1
        self.processing_latency_ms_total += decision.processing_latency_ms
        self.processing_latency_samples += 1

    def record_strategy_error(self) -> None:
        self.strategy_errors_total += 1

    def record_downstream_error(self) -> None:
        self.downstream_errors_total += 1

    def snapshot(self) -> dict[str, float | int | dict[str, int]]:
        avg = (
            self.processing_latency_ms_total / self.processing_latency_samples
            if self.processing_latency_samples
            else 0.0
        )
        return {
            "inputs_received_total": self.inputs_received_total,
            "inputs_evaluated_total": self.inputs_evaluated_total,
            "inputs_accepted_total": self.inputs_accepted_total,
            "inputs_degraded_total": self.inputs_degraded_total,
            "inputs_rejected_total": self.inputs_rejected_total,
            "decisions_emitted_total": self.decisions_emitted_total,
            "no_action_decisions_total": self.no_action_decisions_total,
            "strategy_errors_total": self.strategy_errors_total,
            "downstream_errors_total": self.downstream_errors_total,
            "processing_latency_ms_avg": avg,
            "processing_latency_samples": self.processing_latency_samples,
            "decision_counts": dict(sorted(self.decision_counts.items())),
        }

    def clear(self) -> None:
        self.inputs_received_total = 0
        self.inputs_evaluated_total = 0
        self.inputs_accepted_total = 0
        self.inputs_degraded_total = 0
        self.inputs_rejected_total = 0
        self.decisions_emitted_total = 0
        self.no_action_decisions_total = 0
        self.strategy_errors_total = 0
        self.downstream_errors_total = 0
        self.processing_latency_ms_total = 0.0
        self.processing_latency_samples = 0
        self.decision_counts.clear()
