"""PaperBroker determinism and lifecycle tests (#405)."""

from __future__ import annotations

import pytest
from app.broker import BrokerAdapterClosedError, BrokerCommandOutcome
from app.broker.lifecycle import BrokerAdapterLifecycle
from app.broker.models import CancelExecutableOrder
from tests.support.broker_helpers import paper_broker, submit_executable


@pytest.mark.asyncio
async def test_paper_broker_determinism_same_seed_same_outcomes() -> None:
    first = paper_broker(seed=7)
    second = paper_broker(seed=7)
    await first.start()
    await second.start()
    cmd = submit_executable()
    a = await first.submit(cmd)
    b = await second.submit(cmd)
    assert a.outcome is BrokerCommandOutcome.ACKNOWLEDGED
    assert a.submission_identity == b.submission_identity
    assert a.broker_order_id == b.broker_order_id
    assert len(a.lifecycle_events) == len(b.lifecycle_events) == 2
    assert a.lifecycle_events[0].event_identity == b.lifecycle_events[0].event_identity
    assert a.lifecycle_events[1].event_identity == b.lifecycle_events[1].event_identity


@pytest.mark.asyncio
async def test_paper_broker_duplicate_submit_is_idempotent() -> None:
    broker = paper_broker(seed=1)
    await broker.start()
    cmd = submit_executable()
    first = await broker.submit(cmd)
    second = await broker.submit(cmd)
    assert first.submission_identity == second.submission_identity
    assert broker.metrics.duplicates == 1


@pytest.mark.asyncio
async def test_paper_broker_unknown_outcome_never_implies_accept_or_reject() -> None:
    broker = paper_broker(force_outcome=BrokerCommandOutcome.OUTCOME_UNKNOWN)
    await broker.start()
    result = await broker.submit(submit_executable())
    assert result.outcome is BrokerCommandOutcome.OUTCOME_UNKNOWN
    assert result.broker_order_id is None
    assert result.lifecycle_events == ()
    assert result.fill_events == ()


@pytest.mark.asyncio
async def test_paper_broker_failed_before_send() -> None:
    broker = paper_broker(force_outcome=BrokerCommandOutcome.FAILED_BEFORE_SEND)
    await broker.start()
    result = await broker.submit(submit_executable())
    assert result.outcome is BrokerCommandOutcome.FAILED_BEFORE_SEND
    assert result.broker_order_id is None


@pytest.mark.asyncio
async def test_paper_broker_close_idempotent_and_reject_after_close() -> None:
    broker = paper_broker()
    await broker.start()
    assert broker.lifecycle is BrokerAdapterLifecycle.READY
    await broker.close()
    await broker.close()
    assert broker.lifecycle is BrokerAdapterLifecycle.CLOSED
    with pytest.raises(BrokerAdapterClosedError):
        await broker.submit(submit_executable())


@pytest.mark.asyncio
async def test_paper_broker_cancel_after_close() -> None:
    broker = paper_broker()
    await broker.start()
    submitted = await broker.submit(submit_executable())
    await broker.close()
    with pytest.raises(BrokerAdapterClosedError):
        await broker.cancel(
            CancelExecutableOrder(
                order_id=submit_executable().executable_order.order_id,
                broker_order_id=submitted.broker_order_id,
                cancel_request_id="cancel-1",
                idempotency_key="cancel-1",
            )
        )
