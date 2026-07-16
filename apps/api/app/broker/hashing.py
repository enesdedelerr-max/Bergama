"""Deterministic broker hashing helpers (#405).

Timestamps never participate in identity, hash, version, or transition legality.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from app.broker.identity import (
    BROKER_EVENT_ID_VERSION,
    BROKER_SCHEMA_VERSION,
    SUBMISSION_ID_VERSION,
)
from app.portfolio.decimal import canonical_decimal
from app.strategy.keys import strategy_sha256

if TYPE_CHECKING:
    from app.orders.models import ExecutableOrder, OrderType, TimeInForce


def executable_order_hash(order: ExecutableOrder) -> str:
    return strategy_sha256(
        {
            "account_id": order.account_id.value,
            "broker_schema_version": BROKER_SCHEMA_VERSION,
            "client_order_id": order.client_order_id.value,
            "currency": order.currency,
            "instrument_id": order.instrument.instrument_key,
            "limit_price": canonical_decimal(order.limit_price)
            if order.limit_price is not None
            else None,
            "order_id": order.order_id.value,
            "order_type": order.order_type.value,
            "portfolio_id": order.portfolio_id.value,
            "quantity": canonical_decimal(order.quantity),
            "reference_price": canonical_decimal(order.reference_price),
            "side": order.side.value,
            "time_in_force": order.time_in_force.value,
        }
    )


def build_submission_identity(
    *,
    broker_name: str,
    broker_account_id: str,
    client_order_id: str,
    executable_order_hash_value: str,
) -> str:
    return strategy_sha256(
        {
            "broker_account_id": broker_account_id,
            "broker_name": broker_name,
            "client_order_id": client_order_id,
            "executable_order_hash": executable_order_hash_value,
            "version": SUBMISSION_ID_VERSION,
        }
    )


def build_broker_event_identity(
    *,
    broker_name: str,
    broker_order_id: str,
    broker_event_type: str,
    broker_sequence: int | None,
    broker_event_id: str | None,
) -> str:
    if broker_sequence is not None:
        payload = {
            "broker_event_type": broker_event_type,
            "broker_name": broker_name,
            "broker_order_id": broker_order_id,
            "broker_sequence": broker_sequence,
            "version": BROKER_EVENT_ID_VERSION,
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
            "version": BROKER_EVENT_ID_VERSION,
        }
    return strategy_sha256(payload)


def build_broker_fill_identity(*, broker_fill_id: str | None, fill_id: str | None) -> str:
    if broker_fill_id:
        return strategy_sha256({"broker_fill_id": broker_fill_id})
    if fill_id:
        return strategy_sha256({"fill_id": fill_id})
    msg = "broker_fill_id or fill_id required"
    raise ValueError(msg)


def build_capability_fingerprint(canonical_capabilities: dict[str, object]) -> str:
    return strategy_sha256(canonical_capabilities)


def build_paper_broker_order_id(*, submission_identity: str) -> str:
    return strategy_sha256({"paper_broker_order": submission_identity})


def build_paper_fill_id(*, broker_order_id: str, sequence: int) -> str:
    return strategy_sha256(
        {
            "broker_order_id": broker_order_id,
            "paper_fill_sequence": sequence,
        }
    )


def assert_order_type_supported(order_type: OrderType, supported: tuple[str, ...]) -> None:
    if order_type.value not in supported:
        msg = f"unsupported order_type:{order_type.value}"
        raise ValueError(msg)


def assert_tif_supported(tif: TimeInForce, supported: tuple[str, ...]) -> None:
    if tif.value not in supported:
        msg = f"unsupported time_in_force:{tif.value}"
        raise ValueError(msg)


def decimal_or_none(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return canonical_decimal(value)
