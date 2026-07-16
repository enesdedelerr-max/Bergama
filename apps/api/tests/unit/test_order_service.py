"""Unit tests for OrderManagementService (#404)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.orders.errors import OrderAdmissionError, OrderBrokerPortError, OrderClosedError
from app.orders.models import BrokerLifecycleEventType, OrderStatus
from tests.support.order_helpers import (
    apply_broker,
    apply_fill,
    broker_event,
    cancel_cmd,
    fill_event,
    order_service,
    rejected_assessment,
    submit_cmd,
)


@pytest.mark.asyncio
async def test_service_submit_accept_fill_and_ports() -> None:
    service, broker, fills = order_service()
    result = await service.submit(submit_cmd())
    assert result.next_snapshot.status is OrderStatus.PENDING_SUBMIT
    assert len(broker.commands) == 1
    order_id = result.next_snapshot.order_id

    await service.apply_broker_event(
        apply_broker(
            order_id=order_id,
            expected_version=1,
            event=broker_event(event_type=BrokerLifecycleEventType.SUBMITTED, sequence=1),
        )
    )
    accepted = await service.apply_broker_event(
        apply_broker(
            order_id=order_id,
            expected_version=2,
            event=broker_event(event_type=BrokerLifecycleEventType.ACCEPTED, sequence=2),
        )
    )
    assert accepted.next_snapshot.status is OrderStatus.ACCEPTED
    filled = await service.apply_broker_event(
        apply_fill(
            order_id=order_id,
            expected_version=3,
            fill=fill_event(order_id=order_id, quantity=Decimal("5"), fill_id="full"),
        )
    )
    assert filled.next_snapshot.status is OrderStatus.FILLED
    assert len(fills.fills) == 1

    # duplicate fill
    dup = await service.apply_broker_event(
        apply_fill(
            order_id=order_id,
            expected_version=4,
            fill=fill_event(order_id=order_id, quantity=Decimal("5"), fill_id="full"),
        )
    )
    assert dup.duplicate is True
    assert len(fills.fills) == 1


@pytest.mark.asyncio
async def test_service_rejects_unapproved_and_broker_failure_typed() -> None:
    service, broker, _ = order_service()
    trade, assessment = rejected_assessment()
    with pytest.raises(OrderAdmissionError):
        await service.submit(submit_cmd(trade=trade, assessment=assessment))
    assert broker.commands == ()

    broker.fail_next = RuntimeError("provider boom")
    with pytest.raises(OrderBrokerPortError):
        await service.submit(submit_cmd(client_order_id="client-fail-1"))


@pytest.mark.asyncio
async def test_cancel_race_full_fill_wins() -> None:
    service, _, _ = order_service()
    created = await service.submit(submit_cmd(client_order_id="cancel-race"))
    oid = created.next_snapshot.order_id
    await service.apply_broker_event(
        apply_broker(
            order_id=oid,
            expected_version=1,
            event=broker_event(event_type=BrokerLifecycleEventType.SUBMITTED, sequence=1),
        )
    )
    await service.apply_broker_event(
        apply_broker(
            order_id=oid,
            expected_version=2,
            event=broker_event(event_type=BrokerLifecycleEventType.ACCEPTED, sequence=2),
        )
    )
    pending = await service.request_cancel(cancel_cmd(order_id=oid, expected_version=3))
    assert pending.next_snapshot.status is OrderStatus.CANCEL_PENDING
    filled = await service.apply_broker_event(
        apply_fill(
            order_id=oid,
            expected_version=4,
            fill=fill_event(order_id=oid, quantity=Decimal("5"), fill_id="race-fill"),
        )
    )
    assert filled.next_snapshot.status is OrderStatus.FILLED
    # later cancel ack must not change FILLED
    from app.orders.errors import OrderTerminalMutationError

    with pytest.raises(OrderTerminalMutationError):
        await service.apply_broker_event(
            apply_broker(
                order_id=oid,
                expected_version=5,
                event=broker_event(
                    event_type=BrokerLifecycleEventType.CANCELLED,
                    sequence=3,
                ),
            )
        )


@pytest.mark.asyncio
async def test_close_idempotent() -> None:
    service, _, _ = order_service()
    await service.aclose()
    await service.aclose()
    with pytest.raises(OrderClosedError):
        await service.submit(submit_cmd(client_order_id="after-close"))
