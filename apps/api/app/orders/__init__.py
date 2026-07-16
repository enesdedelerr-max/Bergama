"""Order Management System (#404) — lifecycle only, no broker adapter or portfolio mutation."""

from app.orders.aggregate import OrderAggregate
from app.orders.commands import ApplyBrokerEvent, RequestCancel, SubmitOrder
from app.orders.events import BrokerOrderCommand, BrokerOrderEvent, DomainEvent, FillEvent
from app.orders.identity import ClientOrderId, OrderId
from app.orders.models import (
    ExecutableOrder,
    OrderSide,
    OrderSnapshot,
    OrderStatus,
    OrderType,
    TimeInForce,
)
from app.orders.policies import OrderPolicy
from app.orders.ports import (
    BrokerOrderPort,
    FillEventPort,
    InMemoryBrokerOrderPort,
    InMemoryFillEventPort,
)
from app.orders.repository import InMemoryOrderRepository, OrderRepository
from app.orders.result import OrderMutationResult
from app.orders.service import OrderManagementService, build_order_management_service
from app.orders.transitions import LEGAL_TRANSITIONS, TERMINAL_STATUSES

__all__ = [
    "LEGAL_TRANSITIONS",
    "TERMINAL_STATUSES",
    "ApplyBrokerEvent",
    "BrokerOrderCommand",
    "BrokerOrderEvent",
    "BrokerOrderPort",
    "ClientOrderId",
    "DomainEvent",
    "ExecutableOrder",
    "FillEvent",
    "FillEventPort",
    "InMemoryBrokerOrderPort",
    "InMemoryFillEventPort",
    "InMemoryOrderRepository",
    "OrderAggregate",
    "OrderId",
    "OrderManagementService",
    "OrderMutationResult",
    "OrderPolicy",
    "OrderRepository",
    "OrderSide",
    "OrderSnapshot",
    "OrderStatus",
    "OrderType",
    "RequestCancel",
    "SubmitOrder",
    "TimeInForce",
    "build_order_management_service",
]
