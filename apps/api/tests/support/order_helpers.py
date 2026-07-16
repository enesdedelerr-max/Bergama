"""Shared Order Management System test helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from app.core.clock import FixedClock
from app.orders import (
    ApplyBrokerEvent,
    ClientOrderId,
    FillEvent,
    InMemoryBrokerOrderPort,
    InMemoryFillEventPort,
    OrderManagementService,
    OrderType,
    RequestCancel,
    SubmitOrder,
    TimeInForce,
    build_order_management_service,
)
from app.orders.events import BrokerOrderEvent
from app.orders.models import BrokerLifecycleEventType, OrderSide
from app.risk import RiskFinalAction
from app.risk.engine import build_risk_engine
from tests.support.risk_helpers import empty_snapshot, intent, policy

T0 = datetime(2026, 7, 15, 18, 0, tzinfo=UTC)


def approved_assessment(*, trade=None, snap=None, pol=None, evaluated_at: datetime | None = None):
    trade = trade or intent(expected_portfolio_version=1, quantity_delta=Decimal("5"))
    snap = snap or empty_snapshot(version=1, snapshot_at=T0)
    pol = pol or policy()
    engine = build_risk_engine()
    assessment = engine.evaluate(
        intent=trade,
        snapshot=snap,
        policy=pol,
        evaluated_at=evaluated_at or (T0 + timedelta(seconds=1)),
    )
    assert assessment.final_action is RiskFinalAction.APPROVE
    return trade, assessment


def rejected_assessment():
    trade = intent(expected_portfolio_version=9, quantity_delta=Decimal("5"))
    snap = empty_snapshot(version=1, snapshot_at=T0)
    assessment = build_risk_engine().evaluate(
        intent=trade,
        snapshot=snap,
        policy=policy(),
        evaluated_at=T0 + timedelta(seconds=1),
    )
    assert assessment.final_action is RiskFinalAction.REJECT
    return trade, assessment


def submit_cmd(
    *,
    trade=None,
    assessment=None,
    client_order_id: str = "client-order-1",
    order_type: OrderType = OrderType.MARKET,
    time_in_force: TimeInForce = TimeInForce.DAY,
    limit_price: Decimal | None = None,
    **overrides: Any,
) -> SubmitOrder:
    if trade is None or assessment is None:
        trade, assessment = approved_assessment(trade=trade)
    payload: dict[str, Any] = {
        "intent": trade,
        "assessment": assessment,
        "client_order_id": ClientOrderId(value=client_order_id),
        "order_type": order_type,
        "time_in_force": time_in_force,
        "limit_price": limit_price,
        "idempotency_key": f"submit-{client_order_id}",
        "correlation_id": "corr-order-1",
        "causation_id": "cause-order-1",
    }
    payload.update(overrides)
    return SubmitOrder.model_validate(payload)


def order_service(
    *,
    broker: InMemoryBrokerOrderPort | None = None,
    fills: InMemoryFillEventPort | None = None,
) -> tuple[OrderManagementService, InMemoryBrokerOrderPort, InMemoryFillEventPort]:
    broker_port = broker or InMemoryBrokerOrderPort()
    fill_port = fills or InMemoryFillEventPort()
    service = build_order_management_service(
        clock=FixedClock(T0 + timedelta(minutes=5)),
        broker_port=broker_port,
        fill_port=fill_port,
    )
    return service, broker_port, fill_port


def broker_event(
    *,
    broker_order_id: str = "broker-1",
    event_type: BrokerLifecycleEventType = BrokerLifecycleEventType.ACCEPTED,
    sequence: int | None = 1,
    event_id: str | None = None,
) -> BrokerOrderEvent:
    return BrokerOrderEvent(
        broker_name="paper",
        broker_order_id=broker_order_id,
        broker_event_type=event_type,
        broker_event_sequence=sequence,
        broker_event_id=event_id,
    )


def fill_event(
    *,
    order_id,
    quantity: Decimal = Decimal("2"),
    price: Decimal = Decimal("100"),
    fill_id: str = "fill-1",
    side: OrderSide = OrderSide.BUY,
    instrument=None,
) -> FillEvent:
    trade, _ = approved_assessment()
    inst = instrument or trade.instrument_id
    instant = T0 + timedelta(minutes=10)
    return FillEvent(
        fill_id=fill_id,
        order_id=order_id,
        instrument=inst,
        side=side,
        quantity=quantity,
        price=price,
        fee=Decimal("0"),
        currency="USD",
        occurred_at=instant,
        known_at=instant + timedelta(milliseconds=1),
        ingested_at=instant + timedelta(milliseconds=2),
        idempotency_key=f"fill-key-{fill_id}",
    )


def apply_broker(*, order_id, expected_version: int, event: BrokerOrderEvent) -> ApplyBrokerEvent:
    return ApplyBrokerEvent(
        order_id=order_id,
        expected_version=expected_version,
        broker_event=event,
        idempotency_key=f"broker-{event.event_identity}",
    )


def apply_fill(*, order_id, expected_version: int, fill: FillEvent) -> ApplyBrokerEvent:
    return ApplyBrokerEvent(
        order_id=order_id,
        expected_version=expected_version,
        fill_event=fill,
        idempotency_key=f"fill-apply-{fill.fill_identity}",
    )


def cancel_cmd(
    *,
    order_id,
    expected_version: int,
    cancel_request_id: str = "cancel-1",
) -> RequestCancel:
    return RequestCancel(
        order_id=order_id,
        cancel_request_id=cancel_request_id,
        expected_version=expected_version,
        idempotency_key=f"cancel-{cancel_request_id}",
    )
