"""Pure average-cost portfolio accounting helpers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.portfolio.decimal import (
    ZERO,
    quantize_money,
    quantize_pnl,
    quantize_quantity,
)
from app.portfolio.errors import PortfolioAccountingInvariantError, PortfolioShortingDisabledError
from app.portfolio.models import FillApplied, FillSide, PositionState
from app.portfolio.policies import PortfolioPolicy


@dataclass(frozen=True, slots=True)
class FillAccountingResult:
    next_position: PositionState | None
    cash_delta: Decimal
    realized_pnl_delta: Decimal
    quantity_delta: Decimal
    opened: bool
    closed: bool
    reversed: bool


def apply_fill_to_position(
    *,
    position: PositionState | None,
    fill: FillApplied,
    policy: PortfolioPolicy,
) -> FillAccountingResult:
    signed_qty = fill.quantity if fill.side is FillSide.BUY else -fill.quantity
    old_qty = position.quantity if position is not None else ZERO
    old_avg = position.average_cost if position is not None else ZERO
    cash_delta = quantize_money(-(signed_qty * fill.price) - fill.fee)
    realized = ZERO

    if old_qty == ZERO:
        new_qty = signed_qty
        if new_qty < ZERO and not policy.allow_short_positions:
            raise PortfolioShortingDisabledError(detail=fill.instrument.instrument_key)
        avg = _opening_average_cost(fill=fill, quantity=abs(new_qty))
        next_position = _position_from_fill(fill, quantity=new_qty, average_cost=avg)
        return FillAccountingResult(
            next_position=next_position,
            cash_delta=cash_delta,
            realized_pnl_delta=ZERO,
            quantity_delta=signed_qty,
            opened=True,
            closed=False,
            reversed=False,
        )

    if _same_side(old_qty, signed_qty):
        new_qty = quantize_quantity(old_qty + signed_qty)
        if new_qty == ZERO:
            raise PortfolioAccountingInvariantError(detail="same_side_zero")
        avg = _weighted_average_cost(
            old_quantity=abs(old_qty),
            old_average_cost=old_avg,
            fill=fill,
            added_quantity=abs(signed_qty),
        )
        assert position is not None
        next_position = position.model_copy(update={"quantity": new_qty, "average_cost": avg})
        return FillAccountingResult(
            next_position=next_position,
            cash_delta=cash_delta,
            realized_pnl_delta=ZERO,
            quantity_delta=signed_qty,
            opened=False,
            closed=False,
            reversed=False,
        )

    closing_qty = min(abs(old_qty), abs(signed_qty))
    remaining_qty = quantize_quantity(old_qty + signed_qty)
    fee_for_close, fee_for_open = _allocate_fee(
        fill.fee,
        close_quantity=closing_qty,
        total=fill.quantity,
    )
    if old_qty > ZERO and signed_qty < ZERO:
        realized = quantize_pnl((fill.price - old_avg) * closing_qty - fee_for_close)
    elif old_qty < ZERO and signed_qty > ZERO:
        realized = quantize_pnl((old_avg - fill.price) * closing_qty - fee_for_close)
    else:
        raise PortfolioAccountingInvariantError(detail="invalid_signs")

    closed = remaining_qty == ZERO
    reversed_ = old_qty != ZERO and _opposite_side(old_qty, remaining_qty)
    if remaining_qty < ZERO and not policy.allow_short_positions:
        raise PortfolioShortingDisabledError(detail=fill.instrument.instrument_key)

    if remaining_qty == ZERO:
        flat_position = None
        if not policy.cleanup_zero_positions:
            assert position is not None
            flat_position = position.model_copy(update={"quantity": ZERO})
        return FillAccountingResult(
            next_position=flat_position,
            cash_delta=cash_delta,
            realized_pnl_delta=realized,
            quantity_delta=signed_qty,
            opened=False,
            closed=True,
            reversed=False,
        )

    if reversed_:
        avg = (
            fill.price
            if remaining_qty < ZERO
            else _opening_average_cost(
                fill=fill,
                quantity=abs(remaining_qty),
                opening_fee=fee_for_open,
            )
        )
        next_position = _position_from_fill(fill, quantity=remaining_qty, average_cost=avg)
    else:
        assert position is not None
        next_position = position.model_copy(
            update={"quantity": remaining_qty, "average_cost": old_avg}
        )
    return FillAccountingResult(
        next_position=next_position,
        cash_delta=cash_delta,
        realized_pnl_delta=realized,
        quantity_delta=signed_qty,
        opened=False,
        closed=closed,
        reversed=reversed_,
    )


def mark_position(position: PositionState, *, mark_price: Decimal) -> PositionState:
    quantity = position.quantity
    market_value = quantize_money(quantity * mark_price)
    if quantity > ZERO:
        unrealized = quantize_pnl((mark_price - position.average_cost) * quantity)
    elif quantity < ZERO:
        unrealized = quantize_pnl((position.average_cost - mark_price) * abs(quantity))
    else:
        unrealized = ZERO
    return position.model_copy(
        update={
            "last_mark_price": mark_price,
            "market_value": market_value,
            "unrealized_pnl": unrealized,
        }
    )


def _position_from_fill(
    fill: FillApplied,
    *,
    quantity: Decimal,
    average_cost: Decimal,
) -> PositionState:
    return PositionState(
        instrument=fill.instrument,
        currency=fill.currency,
        quantity=quantity,
        average_cost=average_cost,
        market_value=ZERO,
        unrealized_pnl=ZERO,
    )


def _opening_average_cost(
    *,
    fill: FillApplied,
    quantity: Decimal,
    opening_fee: Decimal | None = None,
) -> Decimal:
    fee = fill.fee if opening_fee is None else opening_fee
    if fill.side is FillSide.BUY:
        return quantize_money(((fill.price * quantity) + fee) / quantity)
    return fill.price


def _weighted_average_cost(
    *,
    old_quantity: Decimal,
    old_average_cost: Decimal,
    fill: FillApplied,
    added_quantity: Decimal,
) -> Decimal:
    if fill.side is FillSide.BUY:
        new_cost = (old_quantity * old_average_cost) + (fill.price * added_quantity) + fill.fee
    else:
        new_cost = (old_quantity * old_average_cost) + (fill.price * added_quantity)
    return quantize_money(new_cost / (old_quantity + added_quantity))


def _allocate_fee(
    fee: Decimal,
    *,
    close_quantity: Decimal,
    total: Decimal,
) -> tuple[Decimal, Decimal]:
    if fee == ZERO:
        return ZERO, ZERO
    close_fee = quantize_money(fee * (close_quantity / total))
    open_fee = quantize_money(fee - close_fee)
    return close_fee, open_fee


def _same_side(left: Decimal, right: Decimal) -> bool:
    return (left > ZERO and right > ZERO) or (left < ZERO and right < ZERO)


def _opposite_side(left: Decimal, right: Decimal) -> bool:
    return (left > ZERO and right < ZERO) or (left < ZERO and right > ZERO)
