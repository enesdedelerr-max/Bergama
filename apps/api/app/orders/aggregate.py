"""Pure OrderAggregate — domain-only order lifecycle transitions (#404)."""

from __future__ import annotations

from datetime import datetime

from app.orders.audit import OrderAuditRecord
from app.orders.commands import ApplyBrokerEvent, RequestCancel, SubmitOrder
from app.orders.errors import (
    OrderAdmissionError,
    OrderIllegalTransitionError,
    OrderOutOfOrderEventError,
    OrderOverfillError,
    OrderTerminalMutationError,
)
from app.orders.events import (
    BrokerCommandType,
    BrokerOrderCommand,
    DomainEvent,
    DomainEventType,
    FillEvent,
)
from app.orders.hashing import build_order_id, build_transition_id
from app.orders.identity import OrderId
from app.orders.models import (
    BrokerLifecycleEventType,
    ExecutableOrder,
    FillRecord,
    OrderIntentReference,
    OrderMutationOutcome,
    OrderSnapshot,
    OrderStatus,
    absolute_quantity,
    side_from_intent,
)
from app.orders.policies import OrderPolicy
from app.orders.result import OrderMutationResult
from app.orders.transitions import (
    CANCELLABLE_STATUSES,
    is_terminal,
    require_legal_transition,
)
from app.portfolio.decimal import ZERO, quantize_money, quantize_price, quantize_quantity
from app.risk.models import RiskFinalAction


class OrderAggregate:
    """Clock-free, repository-free, broker-free order lifecycle aggregate."""

    def __init__(self, snapshot: OrderSnapshot | None, *, policy: OrderPolicy) -> None:
        self._snapshot = snapshot
        self._policy = policy

    @property
    def snapshot(self) -> OrderSnapshot | None:
        return self._snapshot

    def submit(self, command: SubmitOrder, *, created_at: datetime) -> OrderMutationResult:
        self._admit(command)
        intent = command.intent
        qty = absolute_quantity(intent.signed_quantity_delta)
        side = side_from_intent(intent.direction, intent.signed_quantity_delta)
        order_id = OrderId(
            value=build_order_id(
                intent=intent,
                assessment=command.assessment,
                client_order_id=command.client_order_id,
                order_type=command.order_type,
                time_in_force=command.time_in_force,
                side=side,
                quantity=qty,
                limit_price=command.limit_price,
            )
        )
        if self._snapshot is not None:
            if self._snapshot.order_id.value == order_id.value:
                return self._duplicate(command.idempotency_key, kind="command")
            raise OrderAdmissionError(detail="order_already_exists")

        intent_ref = OrderIntentReference(
            intent_id=intent.intent_id,
            assessment_id=command.assessment.assessment_id,
            assessment_hash=command.assessment.assessment_hash,
            policy_id=command.assessment.policy_id,
            policy_version=command.assessment.policy_version,
            policy_fingerprint=command.assessment.policy_fingerprint,
            portfolio_version=command.assessment.portfolio_version,
            strategy_decision_id=intent.strategy_decision_id,
            strategy_action=intent.strategy_action.value if intent.strategy_action else None,
            strategy_run_id=intent.strategy_run_id,
        )
        previous_version = 0
        next_version = 1
        transition_type = "submit"
        transition_id = build_transition_id(
            order_id=order_id.value,
            previous_version=previous_version,
            next_version=next_version,
            transition_type=transition_type,
        )
        next_status = OrderStatus.PENDING_SUBMIT
        snapshot = OrderSnapshot(
            order_id=order_id,
            client_order_id=command.client_order_id,
            account_id=intent.account_id,
            portfolio_id=intent.portfolio_id,
            instrument=intent.instrument_id,
            side=side,
            quantity=qty,
            order_type=command.order_type,
            time_in_force=command.time_in_force,
            limit_price=command.limit_price,
            currency=intent.currency,
            reference_price=intent.reference_price,
            status=next_status,
            order_version=next_version,
            intent_reference=intent_ref,
            remaining_quantity=qty,
            correlation_id=command.correlation_id or intent.correlation_id,
            causation_id=command.causation_id or intent.causation_id,
            safe_metadata=command.safe_metadata,
            created_at=created_at,
            updated_at=created_at,
            last_transition_id=transition_id,
        )
        executable = ExecutableOrder(
            order_id=order_id,
            client_order_id=command.client_order_id,
            account_id=intent.account_id,
            portfolio_id=intent.portfolio_id,
            instrument=intent.instrument_id,
            side=side,
            quantity=qty,
            order_type=command.order_type,
            time_in_force=command.time_in_force,
            limit_price=command.limit_price,
            currency=intent.currency,
            reference_price=intent.reference_price,
            correlation_id=snapshot.correlation_id,
            causation_id=snapshot.causation_id,
        )
        domain_events = (
            DomainEvent(
                event_type=DomainEventType.ORDER_CREATED,
                order_id=order_id,
                transition_id=transition_id,
                previous_status=None,
                next_status=OrderStatus.CREATED,
                previous_version=previous_version,
                next_version=next_version,
                correlation_id=snapshot.correlation_id,
                causation_id=snapshot.causation_id,
            ),
            DomainEvent(
                event_type=DomainEventType.ORDER_SUBMIT_REQUESTED,
                order_id=order_id,
                transition_id=transition_id,
                previous_status=OrderStatus.CREATED,
                next_status=next_status,
                previous_version=previous_version,
                next_version=next_version,
                correlation_id=snapshot.correlation_id,
                causation_id=snapshot.causation_id,
            ),
        )
        broker_commands = (
            BrokerOrderCommand(
                command_type=BrokerCommandType.SUBMIT,
                order_id=order_id,
                executable_order=executable,
                correlation_id=snapshot.correlation_id,
                causation_id=snapshot.causation_id,
            ),
        )
        audit = OrderAuditRecord(
            order_id=order_id,
            previous_version=previous_version,
            next_version=next_version,
            previous_status=None,
            next_status=next_status,
            transition_id=transition_id,
            command_or_event_key=command.idempotency_key,
            assessment_id=command.assessment.assessment_id,
            outcome=OrderMutationOutcome.APPLIED,
            correlation_id=snapshot.correlation_id,
            causation_id=snapshot.causation_id,
            recorded_at=created_at,
        )
        return OrderMutationResult(
            outcome=OrderMutationOutcome.APPLIED,
            duplicate=False,
            next_snapshot=snapshot,
            broker_commands=broker_commands,
            domain_events=domain_events,
            fill_events=(),
            audit_records=(audit,),
            metrics={"orders_created": 1, "submit_requested": 1},
            transition_id=transition_id,
            idempotency_key=command.idempotency_key,
        )

    def request_cancel(
        self,
        command: RequestCancel,
        *,
        updated_at: datetime,
    ) -> OrderMutationResult:
        snapshot = self._require_snapshot()
        if snapshot.order_id.value != command.order_id.value:
            raise OrderAdmissionError(detail="order_id_mismatch")
        if is_terminal(snapshot.status):
            raise OrderTerminalMutationError(detail=snapshot.status.value)
        if snapshot.status not in CANCELLABLE_STATUSES:
            raise OrderIllegalTransitionError(detail=f"{snapshot.status.value}->CANCEL_PENDING")
        return self._transition(
            next_status=OrderStatus.CANCEL_PENDING,
            transition_type="cancel_requested",
            idempotency_key=command.idempotency_key,
            updated_at=updated_at,
            domain_event_type=DomainEventType.CANCEL_REQUESTED,
            broker_commands=(
                BrokerOrderCommand(
                    command_type=BrokerCommandType.CANCEL,
                    order_id=snapshot.order_id,
                    broker_order_id=snapshot.broker_order_id,
                    cancel_request_id=command.cancel_request_id,
                    correlation_id=command.correlation_id or snapshot.correlation_id,
                    causation_id=command.causation_id or snapshot.causation_id,
                ),
            ),
            correlation_id=command.correlation_id,
            causation_id=command.causation_id,
            assessment_id=snapshot.intent_reference.assessment_id,
        )

    def apply_broker_event(
        self,
        command: ApplyBrokerEvent,
        *,
        updated_at: datetime,
    ) -> OrderMutationResult:
        snapshot = self._require_snapshot()
        if snapshot.order_id.value != command.order_id.value:
            raise OrderAdmissionError(detail="order_id_mismatch")

        if command.fill_event is not None:
            return self._apply_fill(command.fill_event, command.idempotency_key, updated_at)

        assert command.broker_event is not None
        event = command.broker_event
        assert event.event_identity is not None
        if event.event_identity in snapshot.seen_broker_event_identities:
            return self._duplicate(command.idempotency_key, kind="broker")

        if event.broker_event_sequence is not None:
            last = snapshot.last_broker_event_sequence
            if last is not None and event.broker_event_sequence <= last:
                raise OrderOutOfOrderEventError(detail="sequence_not_increasing")
            if last is not None and event.broker_event_sequence > last + 1:
                return self._reconciliation(
                    command.idempotency_key,
                    updated_at,
                    reason="sequence_gap",
                    broker_event_identity=event.event_identity,
                    broker_order_id=event.broker_order_id,
                    sequence=event.broker_event_sequence,
                )

        next_status = self._status_for_broker_event(snapshot.status, event.broker_event_type)
        domain_type = self._domain_event_for_broker(event.broker_event_type)
        return self._transition(
            next_status=next_status,
            transition_type=f"broker:{event.broker_event_type.value.lower()}",
            idempotency_key=command.idempotency_key,
            updated_at=updated_at,
            domain_event_type=domain_type,
            broker_commands=(),
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            assessment_id=snapshot.intent_reference.assessment_id,
            broker_event_identity=event.event_identity,
            broker_order_id=event.broker_order_id,
            broker_event_sequence=event.broker_event_sequence,
            extra_domain_events=(
                (
                    DomainEvent(
                        event_type=DomainEventType.BROKER_PORT_FAILED,
                        order_id=snapshot.order_id,
                        transition_id="",  # filled in _transition path via rebuild
                        previous_status=snapshot.status,
                        next_status=next_status,
                        previous_version=snapshot.order_version,
                        next_version=snapshot.order_version + 1,
                        correlation_id=event.correlation_id,
                        causation_id=event.causation_id,
                        safe_metadata={"reason": event.reason_code or "port_failed"},
                    ),
                )
                if event.broker_event_type is BrokerLifecycleEventType.PORT_FAILED
                else ()
            ),
        )

    def _apply_fill(
        self,
        fill: FillEvent,
        idempotency_key: str,
        updated_at: datetime,
    ) -> OrderMutationResult:
        snapshot = self._require_snapshot()
        assert fill.fill_identity is not None
        if fill.fill_identity in snapshot.seen_fill_identities:
            return self._duplicate(idempotency_key, kind="fill")
        if fill.order_id.value != snapshot.order_id.value:
            raise OrderAdmissionError(detail="fill_order_mismatch")
        if fill.instrument.instrument_key != snapshot.instrument.instrument_key:
            raise OrderAdmissionError(detail="fill_instrument_mismatch")
        if fill.side is not snapshot.side:
            raise OrderAdmissionError(detail="fill_side_mismatch")
        if fill.currency != snapshot.currency:
            raise OrderAdmissionError(detail="fill_currency_mismatch")
        if is_terminal(snapshot.status) and snapshot.status is not OrderStatus.FILLED:
            # FILLED already terminal — only exact duplicates allowed (handled above)
            raise OrderTerminalMutationError(detail=snapshot.status.value)

        new_filled = quantize_quantity(snapshot.cumulative_filled_quantity + fill.quantity)
        if new_filled > snapshot.quantity:
            raise OrderOverfillError(detail=str(new_filled))
        remaining = quantize_quantity(snapshot.quantity - new_filled)

        # average fill price
        prior_notional = ZERO
        if snapshot.average_fill_price is not None and snapshot.cumulative_filled_quantity > ZERO:
            prior_notional = quantize_money(
                snapshot.average_fill_price * snapshot.cumulative_filled_quantity
            )
        new_notional = quantize_money(prior_notional + fill.price * fill.quantity)
        avg_price = quantize_price(new_notional / new_filled) if new_filled > ZERO else None
        total_fees = quantize_money(snapshot.total_fees + fill.fee)

        if remaining == ZERO:
            next_status = OrderStatus.FILLED
            domain_type = DomainEventType.ORDER_FILLED
        else:
            next_status = (
                OrderStatus.PARTIALLY_FILLED
                if snapshot.status is not OrderStatus.CANCEL_PENDING
                else OrderStatus.PARTIALLY_FILLED
            )
            # cancel pending with remaining stays CANCEL_PENDING after partial fill
            if snapshot.status is OrderStatus.CANCEL_PENDING and remaining > ZERO:
                next_status = OrderStatus.CANCEL_PENDING
            domain_type = (
                DomainEventType.ORDER_FILLED
                if remaining == ZERO
                else DomainEventType.ORDER_PARTIALLY_FILLED
            )
            if remaining == ZERO:
                next_status = OrderStatus.FILLED

        if snapshot.status is OrderStatus.CANCEL_PENDING and remaining == ZERO:
            next_status = OrderStatus.FILLED
            domain_type = DomainEventType.ORDER_FILLED

        # From ACCEPTED/PARTIALLY_FILLED/CANCEL_PENDING fills are legal
        if snapshot.status in {
            OrderStatus.ACCEPTED,
            OrderStatus.PARTIALLY_FILLED,
            OrderStatus.CANCEL_PENDING,
            OrderStatus.RECONCILIATION_REQUIRED,
        }:
            pass
        elif snapshot.status is OrderStatus.FILLED:
            raise OrderTerminalMutationError(detail="FILLED")
        else:
            require_legal_transition(snapshot.status, next_status)

        fill_record = FillRecord(
            fill_identity=fill.fill_identity,
            fill_id=fill.fill_id,
            broker_fill_id=fill.broker_fill_id,
            quantity=fill.quantity,
            price=fill.price,
            fee=fill.fee,
            occurred_at=fill.occurred_at,
        )
        fills = snapshot.fills + (fill_record,)
        if len(fills) > self._policy.max_fill_history:
            fills = fills[-self._policy.max_fill_history :]
        seen_fills = snapshot.seen_fill_identities + (fill.fill_identity,)
        if len(seen_fills) > self._policy.max_fill_history:
            seen_fills = seen_fills[-self._policy.max_fill_history :]

        return self._transition(
            next_status=next_status,
            transition_type="fill",
            idempotency_key=idempotency_key,
            updated_at=updated_at,
            domain_event_type=domain_type,
            broker_commands=(),
            correlation_id=fill.correlation_id,
            causation_id=fill.causation_id,
            assessment_id=snapshot.intent_reference.assessment_id,
            fill_events=(fill,),
            snapshot_updates={
                "cumulative_filled_quantity": new_filled,
                "remaining_quantity": remaining,
                "average_fill_price": avg_price,
                "total_fees": total_fees,
                "fills": fills,
                "seen_fill_identities": seen_fills,
                "broker_order_id": fill.broker_order_id or snapshot.broker_order_id,
            },
        )

    def _status_for_broker_event(
        self,
        current: OrderStatus,
        event_type: BrokerLifecycleEventType,
    ) -> OrderStatus:
        mapping: dict[BrokerLifecycleEventType, OrderStatus] = {
            BrokerLifecycleEventType.SUBMITTED: OrderStatus.SUBMITTED,
            BrokerLifecycleEventType.ACCEPTED: OrderStatus.ACCEPTED,
            BrokerLifecycleEventType.REJECTED: OrderStatus.REJECTED,
            BrokerLifecycleEventType.CANCELLED: OrderStatus.CANCELLED,
            BrokerLifecycleEventType.EXPIRED: OrderStatus.EXPIRED,
            BrokerLifecycleEventType.PORT_FAILED: OrderStatus.RECONCILIATION_REQUIRED,
        }
        nxt = mapping[event_type]
        if is_terminal(current):
            raise OrderTerminalMutationError(detail=f"{current.value}->{nxt.value}")
        require_legal_transition(current, nxt)
        return nxt

    def _domain_event_for_broker(self, event_type: BrokerLifecycleEventType) -> DomainEventType:
        return {
            BrokerLifecycleEventType.SUBMITTED: DomainEventType.ORDER_SUBMITTED,
            BrokerLifecycleEventType.ACCEPTED: DomainEventType.ORDER_ACCEPTED,
            BrokerLifecycleEventType.REJECTED: DomainEventType.ORDER_REJECTED,
            BrokerLifecycleEventType.CANCELLED: DomainEventType.ORDER_CANCELLED,
            BrokerLifecycleEventType.EXPIRED: DomainEventType.ORDER_EXPIRED,
            BrokerLifecycleEventType.PORT_FAILED: DomainEventType.RECONCILIATION_REQUIRED,
        }[event_type]

    def _transition(
        self,
        *,
        next_status: OrderStatus,
        transition_type: str,
        idempotency_key: str,
        updated_at: datetime,
        domain_event_type: DomainEventType,
        broker_commands: tuple[BrokerOrderCommand, ...],
        correlation_id: str | None,
        causation_id: str | None,
        assessment_id: str | None,
        broker_event_identity: str | None = None,
        broker_order_id: str | None = None,
        broker_event_sequence: int | None = None,
        fill_events: tuple[FillEvent, ...] = (),
        snapshot_updates: dict[str, object] | None = None,
        extra_domain_events: tuple[DomainEvent, ...] = (),
    ) -> OrderMutationResult:
        snapshot = self._require_snapshot()
        require_legal_transition(snapshot.status, next_status)
        previous_version = snapshot.order_version
        next_version = previous_version + 1
        transition_id = build_transition_id(
            order_id=snapshot.order_id.value,
            previous_version=previous_version,
            next_version=next_version,
            transition_type=transition_type,
        )
        seen_broker = snapshot.seen_broker_event_identities
        if broker_event_identity:
            seen_broker = seen_broker + (broker_event_identity,)
            if len(seen_broker) > self._policy.max_broker_event_history:
                seen_broker = seen_broker[-self._policy.max_broker_event_history :]

        updates: dict[str, object] = {
            "status": next_status,
            "order_version": next_version,
            "updated_at": updated_at,
            "last_transition_id": transition_id,
            "seen_broker_event_identities": seen_broker,
            "correlation_id": correlation_id or snapshot.correlation_id,
            "causation_id": causation_id or snapshot.causation_id,
        }
        if broker_order_id:
            updates["broker_order_id"] = broker_order_id
        if broker_event_sequence is not None:
            updates["last_broker_event_sequence"] = broker_event_sequence
        if snapshot_updates:
            updates.update(snapshot_updates)

        next_snapshot = snapshot.model_copy(update=updates)
        domain_event = DomainEvent(
            event_type=domain_event_type,
            order_id=snapshot.order_id,
            transition_id=transition_id,
            previous_status=snapshot.status,
            next_status=next_status,
            previous_version=previous_version,
            next_version=next_version,
            correlation_id=next_snapshot.correlation_id,
            causation_id=next_snapshot.causation_id,
        )
        extras = tuple(
            event.model_copy(update={"transition_id": transition_id})
            for event in extra_domain_events
        )
        # Avoid duplicate RECONCILIATION when PORT_FAILED already mapped
        domain_events = (domain_event,) + tuple(
            e for e in extras if e.event_type is not domain_event_type
        )
        audit = OrderAuditRecord(
            order_id=snapshot.order_id,
            previous_version=previous_version,
            next_version=next_version,
            previous_status=snapshot.status,
            next_status=next_status,
            transition_id=transition_id,
            command_or_event_key=idempotency_key,
            assessment_id=assessment_id,
            broker_event_identity=broker_event_identity,
            outcome=OrderMutationOutcome.APPLIED,
            correlation_id=next_snapshot.correlation_id,
            causation_id=next_snapshot.causation_id,
            recorded_at=updated_at,
        )
        return OrderMutationResult(
            outcome=OrderMutationOutcome.APPLIED,
            duplicate=False,
            next_snapshot=next_snapshot,
            broker_commands=broker_commands,
            domain_events=domain_events,
            fill_events=fill_events,
            audit_records=(audit,),
            metrics={"transition": 1},
            transition_id=transition_id,
            idempotency_key=idempotency_key,
        )

    def _reconciliation(
        self,
        idempotency_key: str,
        updated_at: datetime,
        *,
        reason: str,
        broker_event_identity: str,
        broker_order_id: str,
        sequence: int,
    ) -> OrderMutationResult:
        return self._transition(
            next_status=OrderStatus.RECONCILIATION_REQUIRED,
            transition_type="reconciliation_required",
            idempotency_key=idempotency_key,
            updated_at=updated_at,
            domain_event_type=DomainEventType.RECONCILIATION_REQUIRED,
            broker_commands=(),
            correlation_id=None,
            causation_id=None,
            assessment_id=self._require_snapshot().intent_reference.assessment_id,
            broker_event_identity=broker_event_identity,
            broker_order_id=broker_order_id,
            broker_event_sequence=sequence,
            snapshot_updates={},
        )

    def _duplicate(self, idempotency_key: str, *, kind: str) -> OrderMutationResult:
        snapshot = self._require_snapshot()
        return OrderMutationResult(
            outcome=OrderMutationOutcome.DUPLICATE,
            duplicate=True,
            next_snapshot=snapshot,
            broker_commands=(),
            domain_events=(),
            fill_events=(),
            audit_records=(),
            metrics={f"duplicate_{kind}": 1},
            transition_id=None,
            idempotency_key=idempotency_key,
        )

    def _admit(self, command: SubmitOrder) -> None:
        intent = command.intent
        assessment = command.assessment
        if assessment.final_action is not RiskFinalAction.APPROVE:
            raise OrderAdmissionError(detail=assessment.final_action.value)
        if assessment.intent_id != intent.intent_id:
            raise OrderAdmissionError(detail="intent_id_mismatch")
        if assessment.portfolio_id.value != intent.portfolio_id.value:
            raise OrderAdmissionError(detail="portfolio_id_mismatch")
        if assessment.portfolio_version != intent.expected_portfolio_version:
            raise OrderAdmissionError(detail="portfolio_version_mismatch")

    def _require_snapshot(self) -> OrderSnapshot:
        if self._snapshot is None:
            from app.orders.errors import OrderMissingError

            raise OrderMissingError(detail="no_snapshot")
        return self._snapshot
