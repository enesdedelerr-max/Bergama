"""Integration: OMS + Risk admission; Portfolio untouched (#404)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.orders.errors import OrderAdmissionError
from app.orders.models import BrokerLifecycleEventType, OrderStatus
from app.portfolio import AccountId, PortfolioId
from app.risk.engine import build_risk_engine
from app.risk.models import RiskFinalAction
from tests.support.order_helpers import (
    apply_broker,
    apply_fill,
    broker_event,
    fill_event,
    order_service,
    rejected_assessment,
    submit_cmd,
)
from tests.support.portfolio_helpers import portfolio_service
from tests.support.risk_helpers import empty_snapshot, intent, policy


@pytest.mark.asyncio
async def test_approve_to_fill_leaves_portfolio_untouched() -> None:
    portfolio = portfolio_service()
    await portfolio.create_portfolio(
        account_id=AccountId(value="acct-test"),
        portfolio_id=PortfolioId(value="portfolio-test"),
        snapshot_at=datetime(2026, 7, 15, tzinfo=UTC),
    )
    before = await portfolio.get_snapshot(PortfolioId(value="portfolio-test"))

    service, broker, fills = order_service()
    created = await service.submit(submit_cmd(client_order_id="integ-1"))
    oid = created.next_snapshot.order_id
    assert len(broker.commands) == 1
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
    filled = await service.apply_broker_event(
        apply_fill(
            order_id=oid,
            expected_version=3,
            fill=fill_event(order_id=oid, quantity=Decimal("5"), fill_id="integ-fill"),
        )
    )
    assert filled.next_snapshot.status is OrderStatus.FILLED
    assert len(fills.fills) == 1

    after = await portfolio.get_snapshot(PortfolioId(value="portfolio-test"))
    assert after.portfolio_version == before.portfolio_version
    assert after.positions == before.positions


@pytest.mark.asyncio
async def test_reject_creates_no_order() -> None:
    service, broker, fills = order_service()
    trade, assessment = rejected_assessment()
    with pytest.raises(OrderAdmissionError):
        await service.submit(submit_cmd(trade=trade, assessment=assessment, client_order_id="nope"))
    assert broker.commands == ()
    assert fills.fills == ()


@pytest.mark.asyncio
async def test_risk_engine_not_required_again_after_admission() -> None:
    # Admission uses the provided assessment; OMS does not call RiskEngine.
    trade = intent(expected_portfolio_version=1)
    assessment = build_risk_engine().evaluate(
        intent=trade,
        snapshot=empty_snapshot(version=1, snapshot_at=datetime(2026, 7, 15, 18, 0, tzinfo=UTC)),
        policy=policy(max_snapshot_age_seconds=86_400, max_mark_age_seconds=86_400),
        evaluated_at=datetime(2026, 7, 15, 18, 0, 1, tzinfo=UTC),
    )
    assert assessment.final_action is RiskFinalAction.APPROVE
    service, _, _ = order_service()
    result = await service.submit(
        submit_cmd(trade=trade, assessment=assessment, client_order_id="once")
    )
    assert result.next_snapshot.intent_reference.assessment_id == assessment.assessment_id
