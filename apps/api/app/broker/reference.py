"""Capability validation reference helpers (#405).

OMS/service validates capabilities before provider submission (fail closed).
"""

from __future__ import annotations

from app.broker.capabilities import BrokerCapabilities
from app.broker.errors import BrokerCapabilityMismatchError
from app.orders.models import ExecutableOrder, OrderType, TimeInForce


def validate_before_submit(
    order: ExecutableOrder,
    capabilities: BrokerCapabilities,
) -> None:
    """Fail closed before any provider submission."""
    if not capabilities.supports_order_type(order.order_type):
        raise BrokerCapabilityMismatchError(detail=f"order_type:{order.order_type.value}")
    if not capabilities.supports_tif(order.time_in_force):
        raise BrokerCapabilityMismatchError(detail=f"time_in_force:{order.time_in_force.value}")
    if order.order_type is OrderType.LIMIT and order.limit_price is None:
        raise BrokerCapabilityMismatchError(detail="limit_price_required")
    if order.order_type is OrderType.MARKET and order.limit_price is not None:
        raise BrokerCapabilityMismatchError(detail="market_with_limit_price")


def validate_before_cancel(*, capabilities: BrokerCapabilities) -> None:
    if not capabilities.supports_cancel:
        raise BrokerCapabilityMismatchError(detail="cancel_unsupported")


def require_supported_mvp(capabilities: BrokerCapabilities) -> None:
    """Paper/live must advertise MARKET/LIMIT and DAY/GTC for Sprint 4 MVP."""
    required_types = {OrderType.MARKET, OrderType.LIMIT}
    required_tif = {TimeInForce.DAY, TimeInForce.GTC}
    if not required_types.issubset(set(capabilities.supported_order_types)):
        raise BrokerCapabilityMismatchError(detail="mvp_order_types")
    if not required_tif.issubset(set(capabilities.supported_time_in_force)):
        raise BrokerCapabilityMismatchError(detail="mvp_tif")
