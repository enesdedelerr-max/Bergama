"""Risk evaluation context — derived, immutable computation inputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.portfolio.decimal import ZERO, quantize_money, quantize_quantity
from app.portfolio.models import PortfolioSnapshot, PositionState
from app.risk.models import ProposedTradeIntent
from app.risk.policy import RiskPolicy


@dataclass(frozen=True, slots=True)
class RiskEvaluationContext:
    """Side-effect-free derived values for rule evaluation."""

    intent: ProposedTradeIntent
    snapshot: PortfolioSnapshot
    policy: RiskPolicy
    evaluated_at: datetime
    current_position: PositionState | None
    current_quantity: Decimal
    resulting_quantity: Decimal
    order_notional: Decimal
    resulting_position_notional: Decimal
    existing_instrument_exposure: Decimal
    existing_instrument_signed_exposure: Decimal
    new_instrument_exposure: Decimal
    new_instrument_signed_exposure: Decimal
    resulting_gross_exposure: Decimal
    resulting_net_exposure: Decimal
    concentration_ratio: Decimal | None
    mark_missing: bool
    mark_price: Decimal | None
    mark_at: datetime | None
    skip_remaining: bool = False
    halt: bool = False
    skip_price_dependent: bool = False


def build_evaluation_context(
    *,
    intent: ProposedTradeIntent,
    snapshot: PortfolioSnapshot,
    policy: RiskPolicy,
    evaluated_at: datetime,
) -> RiskEvaluationContext:
    instrument_key = intent.instrument_id.instrument_key
    current_position = next(
        (
            position
            for position in snapshot.positions
            if position.instrument.instrument_key == instrument_key
        ),
        None,
    )
    current_quantity = current_position.quantity if current_position is not None else ZERO
    resulting_quantity = quantize_quantity(current_quantity + intent.signed_quantity_delta)
    order_notional = quantize_money(abs(intent.signed_quantity_delta * intent.reference_price))
    resulting_position_notional = quantize_money(abs(resulting_quantity * intent.reference_price))

    mark_price = current_position.last_mark_price if current_position is not None else None
    mark_at = current_position.last_mark_at if current_position is not None else None
    mark_missing = current_position is not None and (mark_price is None or mark_at is None)

    if current_position is None or mark_missing or mark_price is None:
        existing_instrument_exposure = ZERO
        existing_instrument_signed_exposure = ZERO
    else:
        existing_instrument_exposure = quantize_money(abs(current_quantity * mark_price))
        existing_instrument_signed_exposure = quantize_money(current_quantity * mark_price)

    new_instrument_exposure = resulting_position_notional
    new_instrument_signed_exposure = quantize_money(resulting_quantity * intent.reference_price)
    resulting_gross_exposure = quantize_money(
        snapshot.gross_exposure - existing_instrument_exposure + new_instrument_exposure
    )
    resulting_net_exposure = quantize_money(
        snapshot.net_exposure - existing_instrument_signed_exposure + new_instrument_signed_exposure
    )

    concentration_ratio: Decimal | None
    if resulting_gross_exposure <= ZERO:
        concentration_ratio = None
    else:
        concentration_ratio = new_instrument_exposure / resulting_gross_exposure

    return RiskEvaluationContext(
        intent=intent,
        snapshot=snapshot,
        policy=policy,
        evaluated_at=evaluated_at,
        current_position=current_position,
        current_quantity=current_quantity,
        resulting_quantity=resulting_quantity,
        order_notional=order_notional,
        resulting_position_notional=resulting_position_notional,
        existing_instrument_exposure=existing_instrument_exposure,
        existing_instrument_signed_exposure=existing_instrument_signed_exposure,
        new_instrument_exposure=new_instrument_exposure,
        new_instrument_signed_exposure=new_instrument_signed_exposure,
        resulting_gross_exposure=resulting_gross_exposure,
        resulting_net_exposure=resulting_net_exposure,
        concentration_ratio=concentration_ratio,
        mark_missing=mark_missing,
        mark_price=mark_price,
        mark_at=mark_at,
    )
