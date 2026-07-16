"""Average-cost Portfolio accounting tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.portfolio.aggregate import PortfolioAggregate
from app.portfolio.errors import PortfolioCurrencyMismatchError, PortfolioShortingDisabledError
from app.portfolio.models import FillSide
from app.portfolio.policies import PortfolioPolicy
from tests.support.portfolio_helpers import account_id, fill, mark_update, portfolio_id


def _aggregate(policy: PortfolioPolicy | None = None) -> PortfolioAggregate:
    policy = policy or PortfolioPolicy()
    snapshot = PortfolioAggregate.initial_snapshot(
        account_id=account_id(),
        portfolio_id=portfolio_id(),
        policy=policy,
        snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
    )
    return PortfolioAggregate(snapshot, policy=policy)


def test_open_add_partial_and_full_long_with_average_cost_and_fees() -> None:
    policy = PortfolioPolicy()
    agg = _aggregate(policy)
    opened = agg.apply_fill(fill(idx=1, side=FillSide.BUY, quantity="10", price="100", fee="10"))
    pos = opened.next_snapshot.positions[0]
    assert pos.quantity == Decimal("10.00000000")
    assert pos.average_cost == Decimal("101.000000")
    assert opened.cash_delta.amount == Decimal("-1010.000000")

    added = PortfolioAggregate(opened.next_snapshot, policy=policy).apply_fill(
        fill(idx=2, side=FillSide.BUY, quantity="10", price="110", fee="0")
    )
    pos = added.next_snapshot.positions[0]
    assert pos.quantity == Decimal("20.00000000")
    assert pos.average_cost == Decimal("105.500000")

    partial = PortfolioAggregate(added.next_snapshot, policy=policy).apply_fill(
        fill(idx=3, side=FillSide.SELL, quantity="5", price="120", fee="5")
    )
    pos = partial.next_snapshot.positions[0]
    assert pos.quantity == Decimal("15.00000000")
    assert partial.realized_pnl_delta == Decimal("67.500000")
    assert partial.cash_delta.amount == Decimal("595.000000")

    closed = PortfolioAggregate(partial.next_snapshot, policy=policy).apply_fill(
        fill(idx=4, side=FillSide.SELL, quantity="15", price="100", fee="0")
    )
    assert closed.next_snapshot.positions == ()
    assert closed.position_delta.closed is True
    assert closed.next_snapshot.portfolio_version == 4


def test_long_to_short_reversal_resets_average_cost() -> None:
    policy = PortfolioPolicy(allow_short_positions=True)
    opened = _aggregate(policy).apply_fill(
        fill(idx=1, side=FillSide.BUY, quantity="10", price="100")
    )
    reversed_result = PortfolioAggregate(opened.next_snapshot, policy=policy).apply_fill(
        fill(idx=2, side=FillSide.SELL, quantity="15", price="90")
    )
    pos = reversed_result.next_snapshot.positions[0]
    assert pos.quantity == Decimal("-5.00000000")
    assert pos.average_cost == Decimal("90.000000")
    assert reversed_result.realized_pnl_delta == Decimal("-100.000000")
    assert reversed_result.position_delta.reversed is True


def test_open_add_partial_and_full_short_with_cover_fee_policy() -> None:
    policy = PortfolioPolicy(allow_short_positions=True)
    opened = _aggregate(policy).apply_fill(
        fill(idx=1, side=FillSide.SELL, quantity="10", price="100", fee="5")
    )
    pos = opened.next_snapshot.positions[0]
    assert pos.quantity == Decimal("-10.00000000")
    assert pos.average_cost == Decimal("100.000000")
    assert opened.cash_delta.amount == Decimal("995.000000")

    added = PortfolioAggregate(opened.next_snapshot, policy=policy).apply_fill(
        fill(idx=2, side=FillSide.SELL, quantity="10", price="90")
    )
    assert added.next_snapshot.positions[0].average_cost == Decimal("95.000000")

    covered = PortfolioAggregate(added.next_snapshot, policy=policy).apply_fill(
        fill(idx=3, side=FillSide.BUY, quantity="5", price="80", fee="5")
    )
    assert covered.next_snapshot.positions[0].quantity == Decimal("-15.00000000")
    assert covered.realized_pnl_delta == Decimal("70.000000")
    assert covered.cash_delta.amount == Decimal("-405.000000")

    closed = PortfolioAggregate(covered.next_snapshot, policy=policy).apply_fill(
        fill(idx=4, side=FillSide.BUY, quantity="15", price="95")
    )
    assert closed.next_snapshot.positions == ()
    assert closed.position_delta.closed is True


def test_short_to_long_reversal_resets_average_cost() -> None:
    policy = PortfolioPolicy(allow_short_positions=True)
    opened = _aggregate(policy).apply_fill(
        fill(idx=1, side=FillSide.SELL, quantity="10", price="100")
    )
    reversed_result = PortfolioAggregate(opened.next_snapshot, policy=policy).apply_fill(
        fill(idx=2, side=FillSide.BUY, quantity="15", price="80")
    )
    pos = reversed_result.next_snapshot.positions[0]
    assert pos.quantity == Decimal("5.00000000")
    assert pos.average_cost == Decimal("80.000000")
    assert reversed_result.realized_pnl_delta == Decimal("200.000000")


def test_explicit_mark_to_market_updates_unrealized_pnl_and_exposure() -> None:
    policy = PortfolioPolicy()
    opened = _aggregate(policy).apply_fill(
        fill(idx=1, side=FillSide.BUY, quantity="10", price="100")
    )
    marked = PortfolioAggregate(opened.next_snapshot, policy=policy).apply_mark_price(
        mark_update(idx=2, price="110")
    )
    pos = marked.next_snapshot.positions[0]
    assert pos.last_mark_price == Decimal("110.00000000")
    assert pos.market_value == Decimal("1100.000000")
    assert marked.next_snapshot.unrealized_pnl == Decimal("100.000000")
    assert marked.next_snapshot.gross_exposure == Decimal("1100.000000")


def test_shorting_disabled_and_currency_mismatch_fail_closed() -> None:
    with pytest.raises(PortfolioShortingDisabledError):
        _aggregate().apply_fill(fill(idx=1, side=FillSide.SELL, quantity="1", price="10"))
    bad = fill(idx=2, side=FillSide.BUY, quantity="1", price="10").model_copy(
        update={"currency": "EUR"}
    )
    with pytest.raises(PortfolioCurrencyMismatchError):
        _aggregate().apply_fill(bad)
