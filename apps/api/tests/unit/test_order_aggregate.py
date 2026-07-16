"""Unit tests for OrderAggregate purity (#404)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from app.orders.aggregate import OrderAggregate
from app.orders.errors import OrderAdmissionError, OrderOverfillError
from app.orders.hashing import build_transition_id
from app.orders.models import BrokerLifecycleEventType, OrderStatus
from app.orders.policies import OrderPolicy
from app.risk.models import RiskFinalAction
from tests.support.order_helpers import (
    T0,
    apply_broker,
    apply_fill,
    approved_assessment,
    broker_event,
    cancel_cmd,
    fill_event,
    rejected_assessment,
    submit_cmd,
)


def test_submit_approve_creates_pending_submit() -> None:
    result = OrderAggregate(None, policy=OrderPolicy()).submit(
        submit_cmd(),
        created_at=T0,
    )
    assert result.next_snapshot.status is OrderStatus.PENDING_SUBMIT
    assert result.next_snapshot.order_version == 1
    assert len(result.broker_commands) == 1
    assert result.transition_id == build_transition_id(
        order_id=result.next_snapshot.order_id.value,
        previous_version=0,
        next_version=1,
        transition_type="submit",
    )


def test_reject_and_halt_blocked() -> None:
    trade, assessment = rejected_assessment()
    with pytest.raises(OrderAdmissionError):
        OrderAggregate(None, policy=OrderPolicy()).submit(
            submit_cmd(trade=trade, assessment=assessment),
            created_at=T0,
        )
    # HALT via kill switch
    from app.risk.engine import build_risk_engine
    from tests.support.risk_helpers import empty_snapshot, intent, policy

    trade = intent(expected_portfolio_version=1)
    assessment = build_risk_engine().evaluate(
        intent=trade,
        snapshot=empty_snapshot(version=1, snapshot_at=T0),
        policy=policy(kill_switch_enabled=True),
        evaluated_at=T0 + timedelta(seconds=1),
    )
    assert assessment.final_action is RiskFinalAction.HALT
    with pytest.raises(OrderAdmissionError):
        OrderAggregate(None, policy=OrderPolicy()).submit(
            submit_cmd(trade=trade, assessment=assessment),
            created_at=T0,
        )


def test_quantity_unchanged_on_snapshot() -> None:
    trade, assessment = approved_assessment()
    result = OrderAggregate(None, policy=OrderPolicy()).submit(
        submit_cmd(trade=trade, assessment=assessment),
        created_at=T0,
    )
    assert result.next_snapshot.quantity == abs(trade.signed_quantity_delta)
    assert trade.signed_quantity_delta == Decimal("5")


def test_broker_accept_and_fill_path() -> None:
    created = OrderAggregate(None, policy=OrderPolicy()).submit(submit_cmd(), created_at=T0)
    snap = created.next_snapshot
    submitted = OrderAggregate(snap, policy=OrderPolicy()).apply_broker_event(
        apply_broker(
            order_id=snap.order_id,
            expected_version=1,
            event=broker_event(event_type=BrokerLifecycleEventType.SUBMITTED, sequence=1),
        ),
        updated_at=T0 + timedelta(seconds=1),
    )
    accepted = OrderAggregate(submitted.next_snapshot, policy=OrderPolicy()).apply_broker_event(
        apply_broker(
            order_id=snap.order_id,
            expected_version=2,
            event=broker_event(event_type=BrokerLifecycleEventType.ACCEPTED, sequence=2),
        ),
        updated_at=T0 + timedelta(seconds=2),
    )
    assert accepted.next_snapshot.status is OrderStatus.ACCEPTED
    filled = OrderAggregate(accepted.next_snapshot, policy=OrderPolicy()).apply_broker_event(
        apply_fill(
            order_id=snap.order_id,
            expected_version=3,
            fill=fill_event(order_id=snap.order_id, quantity=Decimal("5"), fill_id="f-full"),
        ),
        updated_at=T0 + timedelta(seconds=3),
    )
    assert filled.next_snapshot.status is OrderStatus.FILLED
    assert filled.next_snapshot.remaining_quantity == 0
    assert len(filled.fill_events) == 1


def test_duplicate_broker_and_fill_mutate_nothing() -> None:
    created = OrderAggregate(None, policy=OrderPolicy()).submit(submit_cmd(), created_at=T0)
    snap = created.next_snapshot
    event = broker_event(event_type=BrokerLifecycleEventType.SUBMITTED, sequence=1)
    first = OrderAggregate(snap, policy=OrderPolicy()).apply_broker_event(
        apply_broker(order_id=snap.order_id, expected_version=1, event=event),
        updated_at=T0,
    )
    dup = OrderAggregate(first.next_snapshot, policy=OrderPolicy()).apply_broker_event(
        apply_broker(order_id=snap.order_id, expected_version=2, event=event),
        updated_at=T0,
    )
    assert dup.duplicate is True
    assert dup.next_snapshot.order_version == first.next_snapshot.order_version


def test_overfill_rejected() -> None:
    created = OrderAggregate(None, policy=OrderPolicy()).submit(submit_cmd(), created_at=T0)
    snap = created.next_snapshot
    accepted = OrderAggregate(snap, policy=OrderPolicy()).apply_broker_event(
        apply_broker(
            order_id=snap.order_id,
            expected_version=1,
            event=broker_event(event_type=BrokerLifecycleEventType.SUBMITTED, sequence=1),
        ),
        updated_at=T0,
    )
    accepted = OrderAggregate(accepted.next_snapshot, policy=OrderPolicy()).apply_broker_event(
        apply_broker(
            order_id=snap.order_id,
            expected_version=2,
            event=broker_event(event_type=BrokerLifecycleEventType.ACCEPTED, sequence=2),
        ),
        updated_at=T0,
    )
    with pytest.raises(OrderOverfillError):
        OrderAggregate(accepted.next_snapshot, policy=OrderPolicy()).apply_broker_event(
            apply_fill(
                order_id=snap.order_id,
                expected_version=3,
                fill=fill_event(order_id=snap.order_id, quantity=Decimal("99"), fill_id="big"),
            ),
            updated_at=T0,
        )


def test_cancel_from_accepted() -> None:
    created = OrderAggregate(None, policy=OrderPolicy()).submit(submit_cmd(), created_at=T0)
    snap = created.next_snapshot
    cur = snap
    for seq, et in (
        (1, BrokerLifecycleEventType.SUBMITTED),
        (2, BrokerLifecycleEventType.ACCEPTED),
    ):
        cur = (
            OrderAggregate(cur, policy=OrderPolicy())
            .apply_broker_event(
                apply_broker(
                    order_id=snap.order_id,
                    expected_version=cur.order_version,
                    event=broker_event(event_type=et, sequence=seq),
                ),
                updated_at=T0,
            )
            .next_snapshot
        )
    cancelled_pending = OrderAggregate(cur, policy=OrderPolicy()).request_cancel(
        cancel_cmd(order_id=snap.order_id, expected_version=cur.order_version),
        updated_at=T0,
    )
    assert cancelled_pending.next_snapshot.status is OrderStatus.CANCEL_PENDING
    assert len(cancelled_pending.broker_commands) == 1
