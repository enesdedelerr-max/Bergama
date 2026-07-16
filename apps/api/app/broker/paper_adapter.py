"""Deterministic PaperBroker adapter (#405).

Same ExecutableOrder + paper policy + fixed clock + fixed seed →
same broker events, outcomes, and identities. Never owns OMS state.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.broker.audit import BrokerAuditRecord, InMemoryBrokerAuditSink
from app.broker.capabilities import BrokerCapabilities, paper_broker_capabilities
from app.broker.errors import (
    BrokerAdapterClosedError,
    BrokerCapabilityMismatchError,
    BrokerError,
    BrokerUnknownOutcomeError,
    BrokerValidationError,
)
from app.broker.hashing import (
    build_paper_broker_order_id,
    build_paper_fill_id,
    build_submission_identity,
    executable_order_hash,
)
from app.broker.identity import BrokerAccountId, BrokerIdentity, BrokerName
from app.broker.lifecycle import BrokerAdapterLifecycle
from app.broker.metrics import BrokerMetrics
from app.broker.models import (
    BrokerCancelResult,
    BrokerFillEvent,
    BrokerLifecycleEvent,
    BrokerLifecycleEventType,
    BrokerSubmissionResult,
    CancelExecutableOrder,
    SubmitExecutableOrder,
)
from app.broker.outcomes import BrokerCommandOutcome
from app.broker.reference import validate_before_cancel, validate_before_submit
from app.core.clock import Clock
from app.orders.events import BrokerCommandType, BrokerOrderCommand
from app.orders.identity import OrderId
from app.orders.models import ExecutableOrder, OrderType
from app.portfolio.decimal import ZERO


class PaperBrokerPolicy:
    """Deterministic paper simulation policy (immutable configuration)."""

    def __init__(
        self,
        *,
        auto_accept: bool = True,
        auto_fill_market: bool = False,
        fill_fee: Decimal = ZERO,
        force_outcome: BrokerCommandOutcome | None = None,
    ) -> None:
        self.auto_accept = auto_accept
        self.auto_fill_market = auto_fill_market
        self.fill_fee = fill_fee
        self.force_outcome = force_outcome


class PaperBroker:
    """In-process deterministic paper broker. No network. No OMS mutation."""

    def __init__(
        self,
        *,
        clock: Clock,
        identity: BrokerIdentity | None = None,
        capabilities: BrokerCapabilities | None = None,
        policy: PaperBrokerPolicy | None = None,
        simulation_seed: int = 0,
        audit_sink: InMemoryBrokerAuditSink | None = None,
        metrics: BrokerMetrics | None = None,
    ) -> None:
        self._clock = clock
        self._identity = identity or BrokerIdentity(
            broker_name=BrokerName(value="paper"),
            broker_account_id=BrokerAccountId(value="paper-account-1"),
        )
        self._capabilities = capabilities or paper_broker_capabilities()
        self._policy = policy or PaperBrokerPolicy()
        self._simulation_seed = simulation_seed
        self._audit = audit_sink or InMemoryBrokerAuditSink()
        self._metrics = metrics or BrokerMetrics()
        self._lifecycle = BrokerAdapterLifecycle.CREATED
        self._seen_submissions: set[str] = set()
        self._seen_cancels: set[str] = set()
        self._broker_orders: dict[str, str] = {}
        self._last_results: dict[str, BrokerSubmissionResult] = {}
        self._last_cancels: dict[str, BrokerCancelResult] = {}

    @property
    def lifecycle(self) -> BrokerAdapterLifecycle:
        return self._lifecycle

    @property
    def metrics(self) -> BrokerMetrics:
        return self._metrics

    @property
    def audit_sink(self) -> InMemoryBrokerAuditSink:
        return self._audit

    @property
    def identity(self) -> BrokerIdentity:
        return self._identity

    def capabilities(self) -> BrokerCapabilities:
        return self._capabilities

    async def start(self) -> None:
        if self._lifecycle is BrokerAdapterLifecycle.READY:
            return
        if self._lifecycle is BrokerAdapterLifecycle.CLOSED:
            raise BrokerAdapterClosedError(detail="restart_forbidden")
        self._lifecycle = BrokerAdapterLifecycle.STARTING
        self._metrics.record_lifecycle(self._lifecycle)
        self._lifecycle = BrokerAdapterLifecycle.READY
        self._metrics.record_lifecycle(self._lifecycle)

    async def close(self) -> None:
        if self._lifecycle is BrokerAdapterLifecycle.CLOSED:
            return
        self._lifecycle = BrokerAdapterLifecycle.STOPPING
        self._metrics.record_lifecycle(self._lifecycle)
        self._lifecycle = BrokerAdapterLifecycle.CLOSED
        self._metrics.record_lifecycle(self._lifecycle)

    async def submit(self, command: SubmitExecutableOrder) -> BrokerSubmissionResult:
        self._metrics.commands_evaluated += 1
        self._metrics.submits += 1
        self._ensure_ready()
        order = command.executable_order
        try:
            validate_before_submit(order, self._capabilities)
        except BrokerCapabilityMismatchError:
            self._metrics.capability_mismatches += 1
            raise

        order_hash = executable_order_hash(order)
        submission_id = build_submission_identity(
            broker_name=self._identity.broker_name.value,
            broker_account_id=self._identity.broker_account_id.value,
            client_order_id=order.client_order_id.value,
            executable_order_hash_value=order_hash,
        )
        if submission_id in self._seen_submissions:
            self._metrics.duplicates += 1
            cached = self._last_results[submission_id]
            return cached

        if self._policy.force_outcome is not None:
            result = self._forced_submission_result(
                command,
                submission_id=submission_id,
                outcome=self._policy.force_outcome,
            )
            self._remember_submission(submission_id, result)
            return result

        broker_order_id = build_paper_broker_order_id(submission_identity=submission_id)
        now = self._clock.now()
        events: list[BrokerLifecycleEvent] = []
        fills: list[BrokerFillEvent] = []
        # SUBMITTED = command/venue acknowledgement fact for OMS PENDING_SUBMIT → SUBMITTED
        events.append(
            self._lifecycle_event(
                broker_order_id=broker_order_id,
                event_type=BrokerLifecycleEventType.SUBMITTED,
                sequence=1 + self._simulation_seed,
                order=order,
                at=now,
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
            )
        )
        if self._policy.auto_accept:
            events.append(
                self._lifecycle_event(
                    broker_order_id=broker_order_id,
                    event_type=BrokerLifecycleEventType.ACCEPTED,
                    sequence=2 + self._simulation_seed,
                    order=order,
                    at=now,
                    correlation_id=command.correlation_id,
                    causation_id=command.causation_id,
                )
            )
            if self._policy.auto_fill_market and order.order_type is OrderType.MARKET:
                fills.append(self._market_fill(order, broker_order_id=broker_order_id, at=now))

        result = BrokerSubmissionResult(
            outcome=BrokerCommandOutcome.ACKNOWLEDGED,
            submission_identity=submission_id,
            broker_order_id=broker_order_id,
            lifecycle_events=tuple(events),
            fill_events=tuple(fills),
            correlation_id=command.correlation_id,
            causation_id=command.causation_id,
            safe_metadata={"simulation_seed": str(self._simulation_seed)},
        )
        self._broker_orders[order.order_id.value] = broker_order_id
        self._remember_submission(submission_id, result)
        self._record_audit(
            order_id=order.order_id,
            command_kind="submit",
            outcome=result.outcome,
            submission_identity=submission_id,
            broker_order_id=broker_order_id,
            correlation_id=command.correlation_id,
            causation_id=command.causation_id,
            recorded_at=now,
        )
        self._metrics.record_outcome(result.outcome)
        return result

    async def cancel(self, command: CancelExecutableOrder) -> BrokerCancelResult:
        self._metrics.commands_evaluated += 1
        self._metrics.cancels += 1
        self._ensure_ready()
        try:
            validate_before_cancel(capabilities=self._capabilities)
        except BrokerCapabilityMismatchError:
            self._metrics.capability_mismatches += 1
            raise

        if command.cancel_request_id in self._seen_cancels:
            self._metrics.duplicates += 1
            return self._last_cancels[command.cancel_request_id]

        if self._policy.force_outcome is not None:
            result = BrokerCancelResult(
                outcome=self._policy.force_outcome,
                broker_order_id=command.broker_order_id,
                reason_code=self._policy.force_outcome.value.lower(),
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
            )
            self._remember_cancel(command.cancel_request_id, result)
            self._metrics.record_outcome(result.outcome)
            return result

        broker_order_id = command.broker_order_id or self._broker_orders.get(command.order_id.value)
        if broker_order_id is None:
            raise BrokerValidationError(detail="broker_order_id_missing")

        now = self._clock.now()
        event = self._lifecycle_event(
            broker_order_id=broker_order_id,
            event_type=BrokerLifecycleEventType.CANCELLED,
            sequence=1000 + self._simulation_seed,
            order=None,
            order_id=command.order_id,
            at=now,
            correlation_id=command.correlation_id,
            causation_id=command.causation_id,
        )
        result = BrokerCancelResult(
            outcome=BrokerCommandOutcome.ACKNOWLEDGED,
            broker_order_id=broker_order_id,
            lifecycle_events=(event,),
            correlation_id=command.correlation_id,
            causation_id=command.causation_id,
            safe_metadata={"simulation_seed": str(self._simulation_seed)},
        )
        self._remember_cancel(command.cancel_request_id, result)
        self._record_audit(
            order_id=command.order_id,
            command_kind="cancel",
            outcome=result.outcome,
            submission_identity=None,
            broker_order_id=broker_order_id,
            correlation_id=command.correlation_id,
            causation_id=command.causation_id,
            recorded_at=now,
        )
        self._metrics.record_outcome(result.outcome)
        return result

    async def submit_oms_command(self, command: BrokerOrderCommand) -> BrokerSubmissionResult:
        if command.command_type is not BrokerCommandType.SUBMIT:
            raise BrokerValidationError(detail="expected_submit")
        if command.executable_order is None:
            raise BrokerValidationError(detail="executable_order_required")
        return await self.submit(
            SubmitExecutableOrder(
                executable_order=command.executable_order,
                idempotency_key=command.order_id.value,
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
            )
        )

    async def cancel_oms_command(self, command: BrokerOrderCommand) -> BrokerCancelResult:
        if command.command_type is not BrokerCommandType.CANCEL:
            raise BrokerValidationError(detail="expected_cancel")
        if command.cancel_request_id is None:
            raise BrokerValidationError(detail="cancel_request_id_required")
        return await self.cancel(
            CancelExecutableOrder(
                order_id=command.order_id,
                broker_order_id=command.broker_order_id,
                cancel_request_id=command.cancel_request_id,
                idempotency_key=command.cancel_request_id,
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
            )
        )

    def _forced_submission_result(
        self,
        command: SubmitExecutableOrder,
        *,
        submission_id: str,
        outcome: BrokerCommandOutcome,
    ) -> BrokerSubmissionResult:
        if outcome is BrokerCommandOutcome.OUTCOME_UNKNOWN:
            # Explicit unknown: never imply accept/reject.
            self._metrics.record_outcome(outcome)
            result = BrokerSubmissionResult(
                outcome=outcome,
                submission_identity=submission_id,
                broker_order_id=None,
                reason_code="outcome_unknown",
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
            )
            self._record_audit(
                order_id=command.executable_order.order_id,
                command_kind="submit",
                outcome=outcome,
                submission_identity=submission_id,
                broker_order_id=None,
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
                recorded_at=self._clock.now(),
            )
            return result
        if outcome is BrokerCommandOutcome.FAILED_BEFORE_SEND:
            self._metrics.record_outcome(outcome)
            return BrokerSubmissionResult(
                outcome=outcome,
                submission_identity=submission_id,
                reason_code="failed_before_send",
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
            )
        if outcome is BrokerCommandOutcome.REJECTED:
            broker_order_id = build_paper_broker_order_id(submission_identity=submission_id)
            event = self._lifecycle_event(
                broker_order_id=broker_order_id,
                event_type=BrokerLifecycleEventType.REJECTED,
                sequence=1 + self._simulation_seed,
                order=command.executable_order,
                at=self._clock.now(),
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
            )
            self._metrics.record_outcome(outcome)
            return BrokerSubmissionResult(
                outcome=outcome,
                submission_identity=submission_id,
                broker_order_id=broker_order_id,
                lifecycle_events=(event,),
                reason_code="rejected",
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
            )
        if outcome is BrokerCommandOutcome.RECONCILIATION_REQUIRED:
            self._metrics.record_outcome(outcome)
            return BrokerSubmissionResult(
                outcome=outcome,
                submission_identity=submission_id,
                reason_code="reconciliation_required",
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
            )
        raise BrokerUnknownOutcomeError(detail=outcome.value)

    def _lifecycle_event(
        self,
        *,
        broker_order_id: str,
        event_type: BrokerLifecycleEventType,
        sequence: int,
        order: ExecutableOrder | None,
        at: datetime,
        correlation_id: str | None,
        causation_id: str | None,
        order_id: OrderId | None = None,
    ) -> BrokerLifecycleEvent:
        return BrokerLifecycleEvent(
            broker_name=self._identity.broker_name,
            broker_account_id=self._identity.broker_account_id,
            broker_order_id=broker_order_id,
            broker_event_type=event_type,
            broker_sequence=sequence,
            order_id=order.order_id if order is not None else order_id,
            client_order_id=order.client_order_id if order is not None else None,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=at,
            received_at=at,
            safe_metadata={"simulation_seed": str(self._simulation_seed)},
        )

    def _market_fill(
        self,
        order: ExecutableOrder,
        *,
        broker_order_id: str,
        at: datetime,
    ) -> BrokerFillEvent:
        fill_id = build_paper_fill_id(broker_order_id=broker_order_id, sequence=1)
        return BrokerFillEvent(
            broker_name=self._identity.broker_name,
            broker_account_id=self._identity.broker_account_id,
            broker_order_id=broker_order_id,
            broker_fill_id=fill_id,
            fill_id=fill_id,
            order_id=order.order_id,
            instrument=order.instrument,
            side=order.side,
            quantity=order.quantity,
            price=order.reference_price,
            fee=self._policy.fill_fee,
            currency=order.currency,
            occurred_at=at,
            received_at=at,
            correlation_id=order.correlation_id,
            causation_id=order.causation_id,
            safe_metadata={"simulation_seed": str(self._simulation_seed)},
        )

    def _remember_submission(self, submission_id: str, result: BrokerSubmissionResult) -> None:
        self._seen_submissions.add(submission_id)
        self._last_results[submission_id] = result

    def _remember_cancel(self, cancel_request_id: str, result: BrokerCancelResult) -> None:
        self._seen_cancels.add(cancel_request_id)
        self._last_cancels[cancel_request_id] = result

    def _record_audit(
        self,
        *,
        order_id: OrderId | None,
        command_kind: str,
        outcome: BrokerCommandOutcome,
        submission_identity: str | None,
        broker_order_id: str | None,
        correlation_id: str | None,
        causation_id: str | None,
        recorded_at: datetime,
    ) -> None:
        self._audit.record(
            BrokerAuditRecord(
                order_id=order_id,
                command_kind=command_kind,
                outcome=outcome,
                submission_identity=submission_identity,
                broker_order_id=broker_order_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                recorded_at=recorded_at,
            )
        )

    def _ensure_ready(self) -> None:
        if self._lifecycle is BrokerAdapterLifecycle.CLOSED:
            self._metrics.adapter_closed_errors += 1
            raise BrokerAdapterClosedError(detail="closed")
        if self._lifecycle is BrokerAdapterLifecycle.CREATED:
            # Paper has no external resources; lazy-start keeps container sync-safe.
            self._lifecycle = BrokerAdapterLifecycle.READY
            self._metrics.record_lifecycle(self._lifecycle)
            return
        if self._lifecycle is not BrokerAdapterLifecycle.READY:
            raise BrokerAdapterClosedError(detail=f"lifecycle:{self._lifecycle.value}")


class PaperBrokerOrderPort:
    """OMS BrokerOrderCommand → PaperBroker typed results bridge."""

    def __init__(self, paper: PaperBroker) -> None:
        self._paper = paper

    def capabilities(self) -> BrokerCapabilities:
        return self._paper.capabilities()

    async def submit(self, command: BrokerOrderCommand) -> BrokerSubmissionResult:
        try:
            return await self._paper.submit_oms_command(command)
        except BrokerError:
            raise
        except Exception as exc:
            raise BrokerValidationError(detail=type(exc).__name__) from exc

    async def cancel(self, command: BrokerOrderCommand) -> BrokerCancelResult:
        try:
            return await self._paper.cancel_oms_command(command)
        except BrokerError:
            raise
        except Exception as exc:
            raise BrokerValidationError(detail=type(exc).__name__) from exc
