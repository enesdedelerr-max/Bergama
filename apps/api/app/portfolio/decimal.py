"""Portfolio Decimal validation, quantization, and canonical serialization."""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Final

from app.portfolio.errors import PortfolioDecimalError

QUANTITY_QUANTUM: Final[Decimal] = Decimal("0.00000001")
PRICE_QUANTUM: Final[Decimal] = Decimal("0.00000001")
MONEY_QUANTUM: Final[Decimal] = Decimal("0.000001")
PNL_QUANTUM: Final[Decimal] = Decimal("0.000001")
ROUNDING_MODE = ROUND_HALF_EVEN
ZERO: Final[Decimal] = Decimal("0")


def parse_portfolio_decimal(value: object, *, field_name: str) -> Decimal:
    if isinstance(value, float):
        raise PortfolioDecimalError(detail=f"{field_name}:float_not_allowed")
    try:
        decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise PortfolioDecimalError(detail=field_name) from exc
    if not decimal_value.is_finite():
        raise PortfolioDecimalError(detail=f"{field_name}:non_finite")
    return decimal_value


def quantize_quantity(value: Decimal) -> Decimal:
    return _quantize(value, QUANTITY_QUANTUM)


def quantize_price(value: Decimal) -> Decimal:
    return _quantize(value, PRICE_QUANTUM)


def quantize_money(value: Decimal) -> Decimal:
    return _quantize(value, MONEY_QUANTUM)


def quantize_pnl(value: Decimal) -> Decimal:
    return _quantize(value, PNL_QUANTUM)


def canonical_decimal(value: Decimal) -> str:
    if not value.is_finite():
        raise PortfolioDecimalError(detail="canonical:non_finite")
    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text in {"", "-", "-0"} else text


def require_positive(value: Decimal, *, field_name: str) -> Decimal:
    if value <= ZERO:
        raise PortfolioDecimalError(detail=f"{field_name}:must_be_positive")
    return value


def require_non_negative(value: Decimal, *, field_name: str) -> Decimal:
    if value < ZERO:
        raise PortfolioDecimalError(detail=f"{field_name}:must_be_non_negative")
    return value


def _quantize(value: Decimal, quantum: Decimal) -> Decimal:
    if not value.is_finite():
        raise PortfolioDecimalError(detail="quantize:non_finite")
    return value.quantize(quantum, rounding=ROUNDING_MODE)
