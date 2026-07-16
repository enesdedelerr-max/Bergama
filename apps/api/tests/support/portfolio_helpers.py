"""Shared Portfolio Aggregate test helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from app.core.clock import FixedClock
from app.portfolio import AccountId, PortfolioId, PortfolioPolicy
from app.portfolio.models import (
    CashAdjustment,
    CashAdjustmentCommand,
    CashAdjustmentReason,
    FillApplied,
    FillAppliedCommand,
    FillSide,
    MarkPriceUpdate,
    MarkPriceUpdateCommand,
)
from app.portfolio.repository import InMemoryPortfolioRepository
from app.portfolio.service import PortfolioService
from tests.support.market_data_fixtures import instrument

T0 = datetime(2026, 7, 15, 14, 30, tzinfo=UTC)


def account_id(value: str = "acct-test") -> AccountId:
    return AccountId(value=value)


def portfolio_id(value: str = "portfolio-test") -> PortfolioId:
    return PortfolioId(value=value)


def portfolio_service(
    *,
    policy: PortfolioPolicy | None = None,
    repository: InMemoryPortfolioRepository | None = None,
) -> PortfolioService:
    return PortfolioService(
        repository=repository or InMemoryPortfolioRepository(),
        clock=FixedClock(T0 + timedelta(hours=1)),
        policy=policy or PortfolioPolicy(),
    )


def fill(
    *,
    idx: int = 1,
    side: FillSide = FillSide.BUY,
    quantity: Decimal | str = Decimal("10"),
    price: Decimal | str = Decimal("100"),
    fee: Decimal | str = Decimal("0"),
    portfolio: PortfolioId | None = None,
    account: AccountId | None = None,
    instrument_key: str = "bergama:equity:us:aapl",
) -> FillApplied:
    instant = T0 + timedelta(minutes=idx)
    idempotency_portfolio = portfolio.value if portfolio else "portfolio-test"
    return FillApplied(
        event_id=f"fill-event-{idx}",
        idempotency_key=f"portfolio:{idempotency_portfolio}:fill:{idx}",
        account_id=account or account_id(),
        portfolio_id=portfolio or portfolio_id(),
        occurred_at=instant,
        known_at=instant + timedelta(milliseconds=1),
        ingested_at=instant + timedelta(milliseconds=2),
        correlation_id=f"corr-{idx}",
        causation_id=f"cause-{idx}",
        fill_id=f"fill-{idx}",
        instrument=instrument(instrument_key=instrument_key),
        side=side,
        quantity=quantity,
        price=price,
        currency="USD",
        fee=fee,
        safe_metadata={"source": "test"},
    )


def cash_adjustment(
    *,
    idx: int = 1,
    amount: Decimal | str = Decimal("10000"),
    portfolio: PortfolioId | None = None,
    account: AccountId | None = None,
) -> CashAdjustment:
    instant = T0 + timedelta(minutes=idx)
    idempotency_portfolio = portfolio.value if portfolio else "portfolio-test"
    return CashAdjustment(
        event_id=f"cash-event-{idx}",
        idempotency_key=f"portfolio:{idempotency_portfolio}:cash:{idx}",
        account_id=account or account_id(),
        portfolio_id=portfolio or portfolio_id(),
        occurred_at=instant,
        known_at=instant + timedelta(milliseconds=1),
        ingested_at=instant + timedelta(milliseconds=2),
        correlation_id=f"cash-corr-{idx}",
        causation_id=f"cash-cause-{idx}",
        amount=amount,
        currency="USD",
        reason=CashAdjustmentReason.INITIAL_FUNDING,
    )


def mark_update(
    *,
    idx: int = 1,
    price: Decimal | str = Decimal("110"),
    portfolio: PortfolioId | None = None,
    account: AccountId | None = None,
) -> MarkPriceUpdate:
    instant = T0 + timedelta(minutes=idx)
    idempotency_portfolio = portfolio.value if portfolio else "portfolio-test"
    return MarkPriceUpdate(
        event_id=f"mark-event-{idx}",
        idempotency_key=f"portfolio:{idempotency_portfolio}:mark:{idx}",
        account_id=account or account_id(),
        portfolio_id=portfolio or portfolio_id(),
        occurred_at=instant,
        known_at=instant + timedelta(milliseconds=1),
        ingested_at=instant + timedelta(milliseconds=2),
        correlation_id=f"mark-corr-{idx}",
        causation_id=f"mark-cause-{idx}",
        instrument=instrument(),
        mark_price=price,
        currency="USD",
        mark_time=instant,
    )


def fill_command(*, expected_version: int = 0, **overrides: Any) -> FillAppliedCommand:
    return FillAppliedCommand(
        mutation=fill(**overrides),
        expected_version=expected_version,
    )


def cash_adjustment_command(
    *,
    expected_version: int = 0,
    **overrides: Any,
) -> CashAdjustmentCommand:
    return CashAdjustmentCommand(
        mutation=cash_adjustment(**overrides),
        expected_version=expected_version,
    )


def mark_update_command(
    *,
    expected_version: int = 0,
    **overrides: Any,
) -> MarkPriceUpdateCommand:
    return MarkPriceUpdateCommand(
        mutation=mark_update(**overrides),
        expected_version=expected_version,
    )
