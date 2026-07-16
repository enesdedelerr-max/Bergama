"""Unit tests for OMS models (#404)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.orders.errors import OrderDecimalError
from app.orders.identity import ClientOrderId, OrderId
from app.orders.models import ExecutableOrder, OrderSide, OrderStatus, OrderType, TimeInForce
from app.portfolio.identity import AccountId, PortfolioId
from pydantic import ValidationError
from tests.support.market_data_fixtures import instrument
from tests.support.order_helpers import approved_assessment, submit_cmd


def test_status_enum_excludes_replace() -> None:
    names = {s.value for s in OrderStatus}
    assert "REPLACE_PENDING" not in names
    assert "REPLACED" not in names
    assert "RECONCILIATION_REQUIRED" in names


def test_mvp_types_and_tif() -> None:
    assert set(OrderType) == {OrderType.MARKET, OrderType.LIMIT}
    assert set(TimeInForce) == {TimeInForce.DAY, TimeInForce.GTC}


def test_executable_order_immutable_and_rejects_float() -> None:
    trade, _ = approved_assessment()
    with pytest.raises((OrderDecimalError, ValidationError)):
        ExecutableOrder(
            order_id=OrderId(value="a" * 64),
            client_order_id=ClientOrderId(value="c1"),
            account_id=AccountId(value="acct-test"),
            portfolio_id=PortfolioId(value="portfolio-test"),
            instrument=instrument(),
            side=OrderSide.BUY,
            quantity=1.5,  # type: ignore[arg-type]
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
            currency="USD",
            reference_price=Decimal("100"),
        )


def test_limit_requires_price_market_forbids() -> None:
    with pytest.raises(ValidationError):
        submit_cmd(order_type=OrderType.LIMIT, limit_price=None)
    with pytest.raises(ValidationError):
        submit_cmd(order_type=OrderType.MARKET, limit_price=Decimal("10"))


def test_order_id_must_be_sha256() -> None:
    with pytest.raises(ValidationError):
        OrderId(value="not-a-hash")
