"""Bounded process-local Order Management System metrics."""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field

from app.orders.events import DomainEventType
from app.orders.models import OrderMutationOutcome, OrderStatus


@dataclass(slots=True)
class OrderMetrics:
    commands_evaluated: int = 0
    orders_created: int = 0
    submit_requested: int = 0
    submitted: int = 0
    accepted: int = 0
    rejected: int = 0
    partial_fills: int = 0
    full_fills: int = 0
    cancel_requested: int = 0
    cancelled: int = 0
    expired: int = 0
    duplicate_commands: int = 0
    duplicate_broker_events: int = 0
    duplicate_fills: int = 0
    illegal_transitions: int = 0
    overfills: int = 0
    version_conflicts: int = 0
    broker_port_failures: int = 0
    reconciliation_required: int = 0
    latency_ms: deque[float] = field(default_factory=lambda: deque(maxlen=512))
    errors_by_code: Counter[str] = field(default_factory=Counter)

    def observe_latency(self, milliseconds: float) -> None:
        self.latency_ms.append(milliseconds)

    def record_error(self, code: str) -> None:
        self.errors_by_code[code] += 1

    def record_status(self, status: OrderStatus) -> None:
        if status is OrderStatus.PENDING_SUBMIT:
            self.submit_requested += 1
        elif status is OrderStatus.SUBMITTED:
            self.submitted += 1
        elif status is OrderStatus.ACCEPTED:
            self.accepted += 1
        elif status is OrderStatus.REJECTED:
            self.rejected += 1
        elif status is OrderStatus.PARTIALLY_FILLED:
            self.partial_fills += 1
        elif status is OrderStatus.FILLED:
            self.full_fills += 1
        elif status is OrderStatus.CANCEL_PENDING:
            self.cancel_requested += 1
        elif status is OrderStatus.CANCELLED:
            self.cancelled += 1
        elif status is OrderStatus.EXPIRED:
            self.expired += 1
        elif status is OrderStatus.RECONCILIATION_REQUIRED:
            self.reconciliation_required += 1

    def record_domain_event(self, event_type: DomainEventType) -> None:
        if event_type is DomainEventType.ORDER_CREATED:
            self.orders_created += 1
        elif event_type is DomainEventType.BROKER_PORT_FAILED:
            self.broker_port_failures += 1

    def record_outcome(self, outcome: OrderMutationOutcome, *, kind: str) -> None:
        if outcome is OrderMutationOutcome.DUPLICATE:
            if kind == "broker":
                self.duplicate_broker_events += 1
            elif kind == "fill":
                self.duplicate_fills += 1
            else:
                self.duplicate_commands += 1
