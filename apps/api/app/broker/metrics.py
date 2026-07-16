"""Bounded process-local broker metrics (#405). No high-cardinality labels."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.broker.lifecycle import BrokerAdapterLifecycle
from app.broker.outcomes import BrokerCommandOutcome


@dataclass
class BrokerMetrics:
    commands_evaluated: int = 0
    submits: int = 0
    cancels: int = 0
    acknowledged: int = 0
    rejected: int = 0
    failed_before_send: int = 0
    outcome_unknown: int = 0
    reconciliation_required: int = 0
    capability_mismatches: int = 0
    adapter_closed_errors: int = 0
    duplicates: int = 0
    lifecycle_by_state: dict[str, int] = field(default_factory=dict)

    def record_outcome(self, outcome: BrokerCommandOutcome) -> None:
        if outcome is BrokerCommandOutcome.ACKNOWLEDGED:
            self.acknowledged += 1
        elif outcome is BrokerCommandOutcome.REJECTED:
            self.rejected += 1
        elif outcome is BrokerCommandOutcome.FAILED_BEFORE_SEND:
            self.failed_before_send += 1
        elif outcome is BrokerCommandOutcome.OUTCOME_UNKNOWN:
            self.outcome_unknown += 1
        elif outcome is BrokerCommandOutcome.RECONCILIATION_REQUIRED:
            self.reconciliation_required += 1

    def record_lifecycle(self, state: BrokerAdapterLifecycle) -> None:
        key = state.value
        self.lifecycle_by_state[key] = self.lifecycle_by_state.get(key, 0) + 1
