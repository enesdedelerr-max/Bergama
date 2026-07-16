"""PortfolioAggregate deterministic transition tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.portfolio.aggregate import PortfolioAggregate
from app.portfolio.hashing import compute_snapshot_hash
from app.portfolio.models import (
    CashAdjustment,
    FillApplied,
    FillSide,
    MarkPriceUpdate,
    PortfolioMutationOutcome,
    PortfolioMutationType,
)
from app.portfolio.policies import PortfolioPolicy
from tests.support.portfolio_helpers import account_id, cash_adjustment, fill, portfolio_id


def test_initial_snapshot_is_deterministic_and_hash_valid() -> None:
    policy = PortfolioPolicy()
    snapshot_a = PortfolioAggregate.initial_snapshot(
        account_id=account_id(),
        portfolio_id=portfolio_id(),
        policy=policy,
        snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
    )
    snapshot_b = PortfolioAggregate.initial_snapshot(
        account_id=account_id(),
        portfolio_id=portfolio_id(),
        policy=policy,
        snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
    )
    assert snapshot_a == snapshot_b
    assert snapshot_a.snapshot_hash == compute_snapshot_hash(snapshot_a)


def test_successful_mutation_increments_version_once_and_creates_summary_ledger() -> None:
    policy = PortfolioPolicy()
    snapshot = PortfolioAggregate.initial_snapshot(
        account_id=account_id(),
        portfolio_id=portfolio_id(),
        policy=policy,
        snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
    )
    result = PortfolioAggregate(snapshot, policy=policy).apply_cash_adjustment(
        cash_adjustment(idx=1, amount="1000")
    )
    assert result.outcome is PortfolioMutationOutcome.APPLIED
    assert result.next_snapshot.portfolio_version == 1
    assert result.ledger_entries[0].ledger_version == 1
    assert result.ledger_entries[0].portfolio_version == 1
    assert len(result.ledger_entries) == 1
    assert result.cash_delta.amount == Decimal("1000.000000")
    assert result.position_delta.quantity_delta == Decimal("0E-8")


def test_fill_mutation_result_contains_position_cash_and_realized_pnl_deltas() -> None:
    policy = PortfolioPolicy()
    snapshot = PortfolioAggregate.initial_snapshot(
        account_id=account_id(),
        portfolio_id=portfolio_id(),
        policy=policy,
        snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
    )
    first = PortfolioAggregate(snapshot, policy=policy).apply_fill(
        fill(idx=1, side=FillSide.BUY, quantity="10", price="100")
    )
    second = PortfolioAggregate(first.next_snapshot, policy=policy).apply_fill(
        fill(idx=2, side=FillSide.SELL, quantity="5", price="110")
    )
    assert second.mutation_type is PortfolioMutationType.FILL_APPLIED
    assert second.position_delta.quantity_delta == Decimal("-5.00000000")
    assert second.cash_delta.amount == Decimal("550.000000")
    assert second.realized_pnl_delta == Decimal("50.000000")


def test_aggregate_has_no_external_dependency_attributes() -> None:
    aggregate = PortfolioAggregate(
        PortfolioAggregate.initial_snapshot(
            account_id=account_id(),
            portfolio_id=portfolio_id(),
            policy=PortfolioPolicy(),
            snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
        ),
        policy=PortfolioPolicy(),
    )
    assert set(vars(aggregate)) == {"_snapshot", "_policy"}


def test_aggregate_facing_mutations_do_not_carry_expected_version() -> None:
    for model in (FillApplied, CashAdjustment, MarkPriceUpdate):
        assert "expected_version" not in model.model_fields
