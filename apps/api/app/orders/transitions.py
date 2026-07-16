"""Closed OrderStatus transition matrix (#404)."""

from __future__ import annotations

from app.orders.errors import OrderIllegalTransitionError, OrderTerminalMutationError
from app.orders.models import OrderStatus

TERMINAL_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.FILLED,
        OrderStatus.CANCELLED,
        OrderStatus.REJECTED,
        OrderStatus.EXPIRED,
        OrderStatus.FAILED,
    }
)

# RECONCILIATION_REQUIRED is non-terminal for observability but blocks normal mutations
# unless recovering via explicit broker/fill application that clears it — MVP treats it
# as mutation-blocking for submit/cancel, allowing only reconciliation-driving events.

LEGAL_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.CREATED: frozenset({OrderStatus.PENDING_SUBMIT}),
    OrderStatus.PENDING_SUBMIT: frozenset(
        {
            OrderStatus.SUBMITTED,
            OrderStatus.FAILED,
            OrderStatus.REJECTED,
            OrderStatus.RECONCILIATION_REQUIRED,
        }
    ),
    OrderStatus.SUBMITTED: frozenset(
        {
            OrderStatus.ACCEPTED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED,
            OrderStatus.FAILED,
            OrderStatus.RECONCILIATION_REQUIRED,
        }
    ),
    OrderStatus.ACCEPTED: frozenset(
        {
            OrderStatus.PARTIALLY_FILLED,
            OrderStatus.FILLED,
            OrderStatus.CANCEL_PENDING,
            OrderStatus.EXPIRED,
            OrderStatus.RECONCILIATION_REQUIRED,
        }
    ),
    OrderStatus.PARTIALLY_FILLED: frozenset(
        {
            OrderStatus.PARTIALLY_FILLED,
            OrderStatus.FILLED,
            OrderStatus.CANCEL_PENDING,
            OrderStatus.EXPIRED,
            OrderStatus.RECONCILIATION_REQUIRED,
        }
    ),
    OrderStatus.CANCEL_PENDING: frozenset(
        {
            OrderStatus.CANCELLED,
            OrderStatus.PARTIALLY_FILLED,
            OrderStatus.FILLED,
            OrderStatus.RECONCILIATION_REQUIRED,
        }
    ),
    OrderStatus.RECONCILIATION_REQUIRED: frozenset(
        {
            OrderStatus.SUBMITTED,
            OrderStatus.ACCEPTED,
            OrderStatus.PARTIALLY_FILLED,
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED,
            OrderStatus.FAILED,
            OrderStatus.RECONCILIATION_REQUIRED,
        }
    ),
    OrderStatus.FILLED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
    OrderStatus.REJECTED: frozenset(),
    OrderStatus.EXPIRED: frozenset(),
    OrderStatus.FAILED: frozenset(),
}

CANCELLABLE_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.ACCEPTED,
        OrderStatus.PARTIALLY_FILLED,
    }
)


def is_terminal(status: OrderStatus) -> bool:
    return status in TERMINAL_STATUSES


def is_legal_transition(current: OrderStatus, nxt: OrderStatus) -> bool:
    return nxt in LEGAL_TRANSITIONS.get(current, frozenset())


def require_legal_transition(current: OrderStatus, nxt: OrderStatus) -> None:
    if is_terminal(current):
        raise OrderTerminalMutationError(detail=f"{current.value}->{nxt.value}")
    if not is_legal_transition(current, nxt):
        raise OrderIllegalTransitionError(detail=f"{current.value}->{nxt.value}")
