"""Unit tests for OMS repository atomicity (#404)."""

from __future__ import annotations

import pytest
from app.orders.aggregate import OrderAggregate
from app.orders.errors import OrderRepositoryError, OrderVersionConflictError
from app.orders.policies import OrderPolicy
from app.orders.repository import InMemoryOrderRepository, RepositoryFailureStage
from tests.support.order_helpers import T0, submit_cmd


@pytest.mark.asyncio
async def test_compare_and_commit_and_failure_injection() -> None:
    repo = InMemoryOrderRepository()
    result = OrderAggregate(None, policy=OrderPolicy()).submit(submit_cmd(), created_at=T0)
    order_id = result.next_snapshot.order_id
    await repo.reserve_idempotency_key(order_id, result.idempotency_key)
    committed = await repo.compare_and_commit(
        order_id=order_id,
        expected_version=0,
        mutation=result,
        idempotency_key=result.idempotency_key,
    )
    assert committed.next_snapshot.order_version == 1
    loaded = await repo.get_snapshot(order_id)
    assert loaded.order_version == 1

    # version conflict
    result2 = OrderAggregate(None, policy=OrderPolicy()).submit(
        submit_cmd(client_order_id="client-order-2"),
        created_at=T0,
    )
    oid2 = result2.next_snapshot.order_id
    await repo.reserve_idempotency_key(oid2, result2.idempotency_key)
    with pytest.raises(OrderVersionConflictError):
        await repo.compare_and_commit(
            order_id=oid2,
            expected_version=5,
            mutation=result2,
            idempotency_key=result2.idempotency_key,
        )

    # failure injection leaves no partial state for new key
    result3 = OrderAggregate(None, policy=OrderPolicy()).submit(
        submit_cmd(client_order_id="client-order-3"),
        created_at=T0,
    )
    oid3 = result3.next_snapshot.order_id
    await repo.reserve_idempotency_key(oid3, result3.idempotency_key)
    repo.inject_failure_once(RepositoryFailureStage.BEFORE_SNAPSHOT_UPDATE)
    with pytest.raises(OrderRepositoryError):
        await repo.compare_and_commit(
            order_id=oid3,
            expected_version=0,
            mutation=result3,
            idempotency_key=result3.idempotency_key,
        )
    assert await repo.load_snapshot(oid3) is None
