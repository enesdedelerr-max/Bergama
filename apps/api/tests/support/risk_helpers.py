"""Shared Risk Engine test helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from app.portfolio.identity import AccountId, PortfolioId
from app.portfolio.models import CashState, PortfolioSnapshot, PositionState
from app.risk import (
    ProposedTradeIntent,
    RiskEngine,
    TradeDirection,
    build_risk_engine,
    reference_risk_policy,
)
from app.risk.policy import RiskPolicy
from tests.support.market_data_fixtures import instrument

T0 = datetime(2026, 7, 15, 15, 0, tzinfo=UTC)


def account_id(value: str = "acct-test") -> AccountId:
    return AccountId(value=value)


def portfolio_id(value: str = "portfolio-test") -> PortfolioId:
    return PortfolioId(value=value)


def empty_snapshot(
    *,
    version: int = 1,
    snapshot_at: datetime | None = None,
    cash: Decimal = Decimal("100000"),
) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        account_id=account_id(),
        portfolio_id=portfolio_id(),
        base_currency="USD",
        cash=CashState(currency="USD", cash_balance=cash),
        positions=(),
        portfolio_version=version,
        configuration_fingerprint="a" * 64,
        snapshot_at=snapshot_at or T0,
    )


def marked_snapshot(
    *,
    quantity: Decimal = Decimal("10"),
    mark_price: Decimal = Decimal("100"),
    version: int = 3,
    snapshot_at: datetime | None = None,
    mark_at: datetime | None = None,
    instrument_key: str = "bergama:equity:us:aapl",
) -> PortfolioSnapshot:
    mark_time = mark_at or T0
    market_value = abs(quantity * mark_price)
    position = PositionState(
        instrument=instrument(instrument_key=instrument_key),
        currency="USD",
        quantity=quantity,
        average_cost=mark_price,
        last_mark_price=mark_price,
        last_mark_at=mark_time,
        market_value=market_value,
        unrealized_pnl=Decimal("0"),
    )
    return PortfolioSnapshot(
        account_id=account_id(),
        portfolio_id=portfolio_id(),
        base_currency="USD",
        cash=CashState(currency="USD", cash_balance=Decimal("100000")),
        positions=(position,),
        market_value=market_value,
        gross_exposure=market_value,
        net_exposure=quantity * mark_price,
        portfolio_version=version,
        configuration_fingerprint="b" * 64,
        snapshot_at=snapshot_at or T0,
    )


def intent(
    *,
    idx: int = 1,
    quantity_delta: Decimal | str | None = Decimal("5"),
    quantity: Decimal | str | None = None,
    direction: TradeDirection | None = None,
    reference_price: Decimal | str = Decimal("100"),
    expected_portfolio_version: int = 1,
    currency: str = "USD",
    instrument_key: str = "bergama:equity:us:aapl",
    **overrides: Any,
) -> ProposedTradeIntent:
    instant = T0 + timedelta(minutes=idx)
    payload: dict[str, Any] = {
        "intent_id": f"intent-{idx}",
        "portfolio_id": portfolio_id(),
        "account_id": account_id(),
        "instrument_id": instrument(instrument_key=instrument_key),
        "reference_price": reference_price,
        "currency": currency,
        "expected_portfolio_version": expected_portfolio_version,
        "occurred_at": instant,
        "known_at": instant + timedelta(milliseconds=1),
        "submitted_at": instant + timedelta(milliseconds=2),
        "correlation_id": f"corr-{idx}",
        "causation_id": f"cause-{idx}",
        "safe_metadata": {"source": "test"},
    }
    if quantity is not None and direction is not None:
        payload["quantity"] = quantity
        payload["direction"] = direction
    else:
        payload["quantity_delta"] = quantity_delta
    payload.update(overrides)
    return ProposedTradeIntent.model_validate(payload)


def policy(**overrides: Any) -> RiskPolicy:
    return reference_risk_policy(**overrides)


def engine() -> RiskEngine:
    return build_risk_engine()
