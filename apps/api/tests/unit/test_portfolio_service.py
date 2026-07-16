"""PortfolioService orchestration tests."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from app.portfolio.errors import (
    PortfolioClosedError,
    PortfolioLockTimeoutError,
    PortfolioRepositoryError,
)
from app.portfolio.models import FillSide, PortfolioMutationOutcome
from app.portfolio.policies import PortfolioPolicy
from app.portfolio.repository import InMemoryPortfolioRepository, RepositoryFailureStage
from app.portfolio.service import _PortfolioSequencer
from tests.support.portfolio_helpers import (
    account_id,
    cash_adjustment_command,
    fill_command,
    mark_update_command,
    portfolio_id,
    portfolio_service,
)


@pytest.mark.asyncio
async def test_service_create_apply_and_query_snapshot_and_ledger() -> None:
    service = portfolio_service()
    created = await service.create_portfolio(
        account_id=account_id(),
        portfolio_id=portfolio_id(),
        snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
    )
    assert created.portfolio_version == 0
    funding = await service.apply_cash_adjustment(cash_adjustment_command(idx=1, amount="1000"))
    assert funding.next_snapshot.cash.cash_balance == funding.cash_delta.amount
    buy = await service.apply_fill(
        fill_command(
            idx=2,
            side=FillSide.BUY,
            quantity="1",
            price="100",
            expected_version=1,
        )
    )
    assert buy.next_snapshot.portfolio_version == 2
    assert (await service.get_snapshot(portfolio_id())).portfolio_version == 2
    assert len(await service.get_ledger(portfolio_id())) == 2


@pytest.mark.asyncio
async def test_duplicate_fill_cash_and_mark_do_not_change_state_version_or_ledger() -> None:
    service = portfolio_service()
    await service.create_portfolio(
        account_id=account_id(),
        portfolio_id=portfolio_id(),
        snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
    )
    funding = cash_adjustment_command(idx=1, amount="1000")
    first_cash = await service.apply_cash_adjustment(funding)
    duplicate_cash = await service.apply_cash_adjustment(funding)
    assert duplicate_cash.outcome is PortfolioMutationOutcome.DUPLICATE
    assert duplicate_cash.duplicate is True
    assert duplicate_cash.next_snapshot == first_cash.next_snapshot

    buy = fill_command(
        idx=2,
        side=FillSide.BUY,
        quantity="1",
        price="100",
        expected_version=1,
    )
    first_fill = await service.apply_fill(buy)
    duplicate_fill = await service.apply_fill(buy)
    assert duplicate_fill.outcome is PortfolioMutationOutcome.DUPLICATE
    assert duplicate_fill.duplicate is True
    assert duplicate_fill.next_snapshot == first_fill.next_snapshot

    mark = mark_update_command(idx=3, price="101", expected_version=2)
    first_mark = await service.apply_mark_price(mark)
    duplicate_mark = await service.apply_mark_price(mark)
    assert duplicate_mark.outcome is PortfolioMutationOutcome.DUPLICATE
    assert duplicate_mark.duplicate is True
    assert duplicate_mark.next_snapshot == first_mark.next_snapshot
    assert len(await service.get_ledger(portfolio_id())) == 3


@pytest.mark.asyncio
async def test_reservation_released_after_repository_failure() -> None:
    repository = InMemoryPortfolioRepository()
    service = portfolio_service(repository=repository)
    await service.create_portfolio(
        account_id=account_id(),
        portfolio_id=portfolio_id(),
        snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
    )
    repository.inject_failure_once(RepositoryFailureStage.BEFORE_LEDGER_APPEND)
    mutation = fill_command(idx=1, side=FillSide.BUY, quantity="1", price="100")
    with pytest.raises(PortfolioRepositoryError):
        await service.apply_fill(mutation)
    assert repository.reserved_keys(portfolio_id()) == frozenset()
    assert repository.committed_keys(portfolio_id()) == frozenset()
    assert (await service.get_snapshot(portfolio_id())).portfolio_version == 0


@pytest.mark.asyncio
async def test_concurrent_duplicate_fill_commits_once() -> None:
    service = portfolio_service()
    await service.create_portfolio(
        account_id=account_id(),
        portfolio_id=portfolio_id(),
        snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
    )
    mutation = fill_command(idx=1, side=FillSide.BUY, quantity="1", price="100")
    results = await asyncio.gather(service.apply_fill(mutation), service.apply_fill(mutation))
    outcomes = sorted(result.outcome.value for result in results)
    assert outcomes == ["APPLIED", "DUPLICATE"]
    assert (await service.get_snapshot(portfolio_id())).portfolio_version == 1
    assert len(await service.get_ledger(portfolio_id())) == 1


@pytest.mark.asyncio
async def test_different_portfolios_are_isolated() -> None:
    service = portfolio_service(policy=PortfolioPolicy())
    first = portfolio_id("portfolio-one")
    second = portfolio_id("portfolio-two")
    await service.create_portfolio(
        account_id=account_id("acct-one"),
        portfolio_id=first,
        snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
    )
    await service.create_portfolio(
        account_id=account_id("acct-two"),
        portfolio_id=second,
        snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
    )
    await asyncio.gather(
        service.apply_cash_adjustment(
            cash_adjustment_command(idx=1, portfolio=first, account=account_id("acct-one"))
        ),
        service.apply_cash_adjustment(
            cash_adjustment_command(idx=1, portfolio=second, account=account_id("acct-two"))
        ),
    )
    assert (await service.get_snapshot(first)).portfolio_version == 1
    assert (await service.get_snapshot(second)).portfolio_version == 1


@pytest.mark.asyncio
async def test_per_portfolio_lock_timeout_fails_closed_and_cleans_waiter() -> None:
    sequencer = _PortfolioSequencer()
    service = portfolio_service()
    service._sequencer = sequencer  # noqa: SLF001
    service._lock_timeout_seconds = 0.001  # noqa: SLF001
    async with sequencer.locked(portfolio_id()):
        with pytest.raises(PortfolioLockTimeoutError):
            await service.create_portfolio(
                account_id=account_id(),
                portfolio_id=portfolio_id(),
                snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
            )
    assert sequencer.active_lock_count == 0


@pytest.mark.asyncio
async def test_per_portfolio_lock_waiter_cleanup_on_cancellation() -> None:
    sequencer = _PortfolioSequencer()

    async def _wait_for_lock() -> None:
        async with sequencer.locked(portfolio_id()):
            return

    async with sequencer.locked(portfolio_id()):
        task = asyncio.create_task(_wait_for_lock())
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    assert sequencer.active_lock_count == 0


@pytest.mark.asyncio
async def test_service_close_is_idempotent_and_after_close_fails() -> None:
    service = portfolio_service()
    await service.aclose()
    await service.aclose()
    with pytest.raises(PortfolioClosedError):
        await service.apply_fill(fill_command())
