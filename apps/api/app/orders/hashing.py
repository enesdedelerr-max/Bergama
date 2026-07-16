"""Deterministic Order Management System hashing helpers."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from app.orders.identity import ORDER_SCHEMA_VERSION, TRANSITION_ID_VERSION
from app.portfolio.decimal import canonical_decimal
from app.strategy.keys import strategy_sha256

if TYPE_CHECKING:
    from app.orders.identity import ClientOrderId
    from app.orders.models import OrderSide, OrderType, TimeInForce
    from app.risk.models import ProposedTradeIntent, RiskAssessment


def build_order_id(
    *,
    intent: ProposedTradeIntent,
    assessment: RiskAssessment,
    client_order_id: ClientOrderId,
    order_type: OrderType,
    time_in_force: TimeInForce,
    side: OrderSide,
    quantity: Decimal,
    limit_price: Decimal | None,
) -> str:
    return strategy_sha256(
        {
            "account_id": intent.account_id.value,
            "assessment_id": assessment.assessment_id,
            "client_order_id": client_order_id.value,
            "currency": intent.currency,
            "instrument_id": intent.instrument_id.instrument_key,
            "intent_id": intent.intent_id,
            "limit_price": canonical_decimal(limit_price) if limit_price is not None else None,
            "order_schema_version": ORDER_SCHEMA_VERSION,
            "order_type": order_type.value,
            "portfolio_id": intent.portfolio_id.value,
            "quantity": canonical_decimal(quantity),
            "reference_price": canonical_decimal(intent.reference_price),
            "side": side.value,
            "time_in_force": time_in_force.value,
        }
    )


def build_transition_id(
    *,
    order_id: str,
    previous_version: int,
    next_version: int,
    transition_type: str,
) -> str:
    payload = (
        f"{TRANSITION_ID_VERSION}\n"
        f"{order_id}\n"
        f"{previous_version}\n"
        f"{next_version}\n"
        f"{transition_type}"
    )
    return strategy_sha256(payload)


def broker_event_identity(
    *,
    broker_name: str,
    broker_order_id: str,
    broker_event_type: str,
    broker_event_sequence: int | None,
    broker_event_id: str | None,
) -> str:
    if broker_event_sequence is not None:
        payload = {
            "broker_event_sequence": broker_event_sequence,
            "broker_event_type": broker_event_type,
            "broker_name": broker_name,
            "broker_order_id": broker_order_id,
        }
    else:
        if not broker_event_id:
            msg = "broker_event_id required when sequence is unavailable"
            raise ValueError(msg)
        payload = {
            "broker_event_id": broker_event_id,
            "broker_event_type": broker_event_type,
            "broker_name": broker_name,
            "broker_order_id": broker_order_id,
        }
    return strategy_sha256(payload)


def fill_event_identity(*, fill_id: str | None, broker_fill_id: str | None) -> str:
    if fill_id:
        return strategy_sha256({"fill_id": fill_id})
    if broker_fill_id:
        return strategy_sha256({"broker_fill_id": broker_fill_id})
    msg = "fill_id or broker_fill_id required"
    raise ValueError(msg)


def submit_idempotency_key(client_order_id: str, command_key: str | None = None) -> str:
    token = command_key.strip() if command_key else client_order_id
    return f"oms:submit:{token}"


def cancel_idempotency_key(*, order_id: str, cancel_request_id: str) -> str:
    return f"oms:cancel:{order_id}:{cancel_request_id}"


def broker_idempotency_key(event_identity: str) -> str:
    return f"oms:broker:{event_identity}"


def fill_idempotency_key(fill_identity: str) -> str:
    return f"oms:fill:{fill_identity}"
