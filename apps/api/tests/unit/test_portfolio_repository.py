"""In-memory Portfolio repository atomicity tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.portfolio.aggregate import PortfolioAggregate
from app.portfolio.errors import PortfolioRepositoryError, PortfolioVersionConflictError
from app.portfolio.models import FillSide
from app.portfolio.policies import PortfolioPolicy
from app.portfolio.repository import InMemoryPortfolioRepository, RepositoryFailureStage
from tests.support.portfolio_helpers import account_id, fill, portfolio_id


async def _snapshot(policy: PortfolioPolicy):
    return PortfolioAggregate.initial_snapshot(
        account_id=account_id(),
        portfolio_id=portfolio_id(),
        policy=policy,
        snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
    )


@pytest.mark.asyncio
async def test_create_load_snapshot_and_ledger_are_isolated() -> None:
    policy = PortfolioPolicy()
    repo = InMemoryPortfolioRepository()
    first = await _snapshot(policy)
    second = PortfolioAggregate.initial_snapshot(
        account_id=account_id("acct-two"),
        portfolio_id=portfolio_id("portfolio-two"),
        policy=policy,
        snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
    )
    await repo.create_portfolio(first)
    await repo.create_portfolio(second)
    assert await repo.get_snapshot(portfolio_id()) == first
    assert await repo.get_snapshot(portfolio_id("portfolio-two")) == second
    assert await repo.get_ledger(portfolio_id()) == ()


@pytest.mark.asyncio
async def test_idempotency_reservation_and_commit() -> None:
    policy = PortfolioPolicy()
    repo = InMemoryPortfolioRepository()
    snapshot = await _snapshot(policy)
    await repo.create_portfolio(snapshot)
    assert await repo.reserve_idempotency_key(portfolio_id(), "idem-1") is True
    result = PortfolioAggregate(snapshot, policy=policy).apply_fill(fill(idx=1, side=FillSide.BUY))
    await repo.compare_and_commit(
        portfolio_id=portfolio_id(),
        expected_version=0,
        mutation=result,
        idempotency_key="idem-1",
    )
    assert await repo.is_idempotency_committed(portfolio_id(), "idem-1") is True
    assert await repo.reserve_idempotency_key(portfolio_id(), "idem-1") is False


@pytest.mark.asyncio
async def test_version_conflict_commits_nothing() -> None:
    policy = PortfolioPolicy()
    repo = InMemoryPortfolioRepository()
    snapshot = await _snapshot(policy)
    await repo.create_portfolio(snapshot)
    await repo.reserve_idempotency_key(portfolio_id(), "idem-1")
    result = PortfolioAggregate(snapshot, policy=policy).apply_fill(fill(idx=1))
    with pytest.raises(PortfolioVersionConflictError):
        await repo.compare_and_commit(
            portfolio_id=portfolio_id(),
            expected_version=99,
            mutation=result,
            idempotency_key="idem-1",
        )
    assert await repo.get_snapshot(portfolio_id()) == snapshot
    assert await repo.get_ledger(portfolio_id()) == ()
    assert await repo.is_idempotency_committed(portfolio_id(), "idem-1") is False


@pytest.mark.asyncio
async def test_repository_duplicate_compare_and_commit_returns_explicit_duplicate() -> None:
    policy = PortfolioPolicy()
    repo = InMemoryPortfolioRepository()
    snapshot = await _snapshot(policy)
    await repo.create_portfolio(snapshot)
    await repo.reserve_idempotency_key(portfolio_id(), "idem-1")
    result = PortfolioAggregate(snapshot, policy=policy).apply_fill(fill(idx=1))
    await repo.compare_and_commit(
        portfolio_id=portfolio_id(),
        expected_version=0,
        mutation=result,
        idempotency_key="idem-1",
    )
    duplicate = await repo.compare_and_commit(
        portfolio_id=portfolio_id(),
        expected_version=0,
        mutation=result,
        idempotency_key="idem-1",
    )
    assert duplicate.duplicate is True
    assert duplicate.ledger_entries == ()
    assert duplicate.next_snapshot.portfolio_version == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("stage", tuple(RepositoryFailureStage))
async def test_atomic_failure_injection_leaves_no_partial_commit(
    stage: RepositoryFailureStage,
) -> None:
    policy = PortfolioPolicy()
    repo = InMemoryPortfolioRepository()
    snapshot = await _snapshot(policy)
    await repo.create_portfolio(snapshot)
    await repo.reserve_idempotency_key(portfolio_id(), "idem-1")
    repo.inject_failure_once(stage)
    result = PortfolioAggregate(snapshot, policy=policy).apply_fill(fill(idx=1))
    with pytest.raises(PortfolioRepositoryError):
        await repo.compare_and_commit(
            portfolio_id=portfolio_id(),
            expected_version=0,
            mutation=result,
            idempotency_key="idem-1",
        )
    assert await repo.get_snapshot(portfolio_id()) == snapshot
    assert await repo.get_ledger(portfolio_id()) == ()
    assert await repo.is_idempotency_committed(portfolio_id(), "idem-1") is False
