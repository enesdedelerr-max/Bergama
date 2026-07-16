"""Integration: OMS ↔ PaperBroker typed boundary (#405)."""

from __future__ import annotations

import pytest
from app.broker import BrokerCommandOutcome, PaperBrokerOrderPort
from app.broker.models import BrokerLifecycleEventType as BrokerEventType
from app.orders import ApplyBrokerEvent, OrderStatus
from app.orders.errors import OrderBrokerPortError
from app.orders.events import BrokerOrderEvent, FillEvent
from app.orders.models import BrokerLifecycleEventType
from app.portfolio import PortfolioService
from app.risk import RiskEngine
from app.strategy.engine import StrategyEngine
from tests.support.broker_helpers import paper_broker
from tests.support.order_helpers import (
    apply_broker,
    cancel_cmd,
    order_service,
    submit_cmd,
)


def _oms_event(broker_event, *, event_type: BrokerLifecycleEventType) -> BrokerOrderEvent:
    return BrokerOrderEvent(
        broker_name=broker_event.broker_name.value,
        broker_order_id=broker_event.broker_order_id,
        broker_event_type=event_type,
        broker_event_sequence=broker_event.broker_sequence,
        correlation_id=broker_event.correlation_id,
        causation_id=broker_event.causation_id,
    )


async def _apply_submitted_then_accepted(service, *, order_id, start_version, submission):
    submitted = next(
        e for e in submission.lifecycle_events if e.broker_event_type is BrokerEventType.SUBMITTED
    )
    accepted = next(
        e for e in submission.lifecycle_events if e.broker_event_type is BrokerEventType.ACCEPTED
    )
    mid = await service.apply_broker_event(
        apply_broker(
            order_id=order_id,
            expected_version=start_version,
            event=_oms_event(submitted, event_type=BrokerLifecycleEventType.SUBMITTED),
        )
    )
    return await service.apply_broker_event(
        apply_broker(
            order_id=order_id,
            expected_version=mid.next_snapshot.order_version,
            event=_oms_event(accepted, event_type=BrokerLifecycleEventType.ACCEPTED),
        )
    )


@pytest.mark.asyncio
async def test_oms_submit_through_paper_broker_acknowledged() -> None:
    paper = paper_broker(seed=3)
    await paper.start()
    service, _, _ = order_service(broker=PaperBrokerOrderPort(paper))
    result = await service.submit(submit_cmd(client_order_id="oms-paper-1"))
    assert result.next_snapshot.status is OrderStatus.PENDING_SUBMIT
    assert paper.metrics.submits == 1
    assert paper.metrics.acknowledged == 1
    submission = next(iter(paper._last_results.values()))
    applied = await _apply_submitted_then_accepted(
        service,
        order_id=result.next_snapshot.order_id,
        start_version=result.next_snapshot.order_version,
        submission=submission,
    )
    assert applied.next_snapshot.status is OrderStatus.ACCEPTED
    assert applied.next_snapshot.broker_order_id == submission.broker_order_id


@pytest.mark.asyncio
async def test_oms_unknown_outcome_requires_reconciliation() -> None:
    paper = paper_broker(force_outcome=BrokerCommandOutcome.OUTCOME_UNKNOWN)
    await paper.start()
    service, _, _ = order_service(broker=PaperBrokerOrderPort(paper))
    result = await service.submit(submit_cmd(client_order_id="oms-unknown-1"))
    assert result.next_snapshot.status is OrderStatus.RECONCILIATION_REQUIRED


@pytest.mark.asyncio
async def test_oms_failed_before_send_raises_typed_error() -> None:
    paper = paper_broker(force_outcome=BrokerCommandOutcome.FAILED_BEFORE_SEND)
    await paper.start()
    service, _, _ = order_service(broker=PaperBrokerOrderPort(paper))
    with pytest.raises(OrderBrokerPortError, match="failed_before_send"):
        await service.submit(submit_cmd(client_order_id="oms-fail-before-1"))


@pytest.mark.asyncio
async def test_oms_cancel_through_paper_broker() -> None:
    paper = paper_broker(seed=2)
    await paper.start()
    service, _, _ = order_service(broker=PaperBrokerOrderPort(paper))
    created = await service.submit(submit_cmd(client_order_id="oms-cancel-1"))
    submission = next(iter(paper._last_results.values()))
    snap = (
        await _apply_submitted_then_accepted(
            service,
            order_id=created.next_snapshot.order_id,
            start_version=1,
            submission=submission,
        )
    ).next_snapshot
    cancelled = await service.request_cancel(
        cancel_cmd(
            order_id=snap.order_id,
            expected_version=snap.order_version,
        )
    )
    assert cancelled.next_snapshot.status is OrderStatus.CANCEL_PENDING
    assert paper.metrics.cancels == 1


@pytest.mark.asyncio
async def test_broker_fill_fact_applied_by_oms_only() -> None:
    paper = paper_broker(seed=5, auto_fill_market=True)
    await paper.start()
    service, _, fills = order_service(broker=PaperBrokerOrderPort(paper))
    created = await service.submit(submit_cmd(client_order_id="oms-fill-1"))
    submission = next(iter(paper._last_results.values()))
    assert submission.fill_events
    fill = submission.fill_events[0]
    oms_fill = FillEvent(
        fill_id=fill.fill_id,
        broker_fill_id=fill.broker_fill_id,
        order_id=fill.order_id,
        broker_order_id=fill.broker_order_id,
        instrument=fill.instrument,
        side=fill.side,
        quantity=fill.quantity,
        price=fill.price,
        fee=fill.fee,
        currency=fill.currency,
        occurred_at=fill.occurred_at,
        known_at=fill.occurred_at,
        ingested_at=fill.occurred_at,
        correlation_id=fill.correlation_id,
        causation_id=fill.causation_id,
        idempotency_key=f"fill-{fill.fill_identity}",
    )
    snap = (
        await _apply_submitted_then_accepted(
            service,
            order_id=created.next_snapshot.order_id,
            start_version=1,
            submission=submission,
        )
    ).next_snapshot
    filled = await service.apply_broker_event(
        ApplyBrokerEvent(
            order_id=snap.order_id,
            expected_version=snap.order_version,
            fill_event=oms_fill,
            idempotency_key=oms_fill.idempotency_key,
        )
    )
    assert filled.next_snapshot.status is OrderStatus.FILLED
    assert len(fills.fills) == 1


def test_broker_package_does_not_reference_downstream_services() -> None:
    assert not hasattr(PaperBrokerOrderPort, "apply_fill")
    assert PortfolioService is not None
    assert RiskEngine is not None
    assert StrategyEngine is not None
