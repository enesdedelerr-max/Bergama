"""Integration: RiskEngine evaluates PortfolioSnapshot without mutating it (#403)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.portfolio.models import FillSide
from app.risk.models import RiskFinalAction
from tests.support.portfolio_helpers import (
    account_id,
    cash_adjustment_command,
    fill_command,
    mark_update_command,
    portfolio_id,
    portfolio_service,
)
from tests.support.risk_helpers import engine, intent, policy

EVAL_AT = datetime(2026, 7, 15, 16, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_risk_evaluates_live_portfolio_snapshot_without_mutation() -> None:
    service = portfolio_service()
    created = await service.create_portfolio(
        account_id=account_id(),
        portfolio_id=portfolio_id(),
        snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
    )
    assert created.portfolio_version == 0

    await service.apply_cash_adjustment(cash_adjustment_command(idx=1, amount=Decimal("50000")))
    await service.apply_fill(
        fill_command(
            idx=2,
            side=FillSide.BUY,
            quantity=Decimal("10"),
            price=Decimal("100"),
            expected_version=1,
        )
    )
    await service.apply_mark_price(
        mark_update_command(idx=3, price=Decimal("101"), expected_version=2)
    )

    snapshot = await service.get_snapshot(portfolio_id())
    before_hash = snapshot.snapshot_hash
    before_version = snapshot.portfolio_version
    before_qty = snapshot.positions[0].quantity

    assessment = engine().evaluate(
        intent=intent(
            expected_portfolio_version=snapshot.portfolio_version,
            quantity_delta=Decimal("1"),
            reference_price=Decimal("101"),
        ),
        snapshot=snapshot,
        policy=policy(
            max_order_notional=Decimal("100000"),
            max_position_notional=Decimal("100000"),
            max_gross_exposure=Decimal("100000"),
            max_net_exposure=Decimal("100000"),
            max_snapshot_age_seconds=86_400,
            max_mark_age_seconds=86_400,
        ),
        evaluated_at=EVAL_AT,
    )

    after = await service.get_snapshot(portfolio_id())
    assert after.portfolio_version == before_version
    assert after.snapshot_hash == before_hash
    assert after.positions[0].quantity == before_qty
    assert assessment.final_action is RiskFinalAction.APPROVE
    assert assessment.portfolio_version == before_version


@pytest.mark.asyncio
async def test_version_mismatch_does_not_retry_or_mutate_portfolio() -> None:
    service = portfolio_service()
    await service.create_portfolio(
        account_id=account_id(),
        portfolio_id=portfolio_id(),
        snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
    )
    await service.apply_cash_adjustment(cash_adjustment_command(idx=1, amount=Decimal("10000")))
    snapshot = await service.get_snapshot(portfolio_id())

    assessment = engine().evaluate(
        intent=intent(expected_portfolio_version=snapshot.portfolio_version + 5),
        snapshot=snapshot,
        policy=policy(),
        evaluated_at=EVAL_AT,
    )
    assert assessment.final_action is RiskFinalAction.REJECT
    after = await service.get_snapshot(portfolio_id())
    assert after.portfolio_version == snapshot.portfolio_version
