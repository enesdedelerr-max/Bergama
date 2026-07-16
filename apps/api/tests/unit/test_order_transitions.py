"""Unit tests for OMS transition matrix (#404)."""

from __future__ import annotations

import pytest
from app.orders.errors import OrderIllegalTransitionError, OrderTerminalMutationError
from app.orders.models import OrderStatus
from app.orders.transitions import (
    LEGAL_TRANSITIONS,
    TERMINAL_STATUSES,
    is_legal_transition,
    require_legal_transition,
)


def test_legal_matrix_locked() -> None:
    assert OrderStatus.CREATED in LEGAL_TRANSITIONS
    assert OrderStatus.PENDING_SUBMIT in LEGAL_TRANSITIONS[OrderStatus.CREATED]
    assert OrderStatus.SUBMITTED in LEGAL_TRANSITIONS[OrderStatus.PENDING_SUBMIT]
    assert OrderStatus.ACCEPTED in LEGAL_TRANSITIONS[OrderStatus.SUBMITTED]
    assert OrderStatus.FILLED in LEGAL_TRANSITIONS[OrderStatus.ACCEPTED]
    assert OrderStatus.CANCEL_PENDING in LEGAL_TRANSITIONS[OrderStatus.ACCEPTED]
    assert OrderStatus.CANCELLED in LEGAL_TRANSITIONS[OrderStatus.CANCEL_PENDING]
    assert "REPLACE_PENDING" not in OrderStatus.__members__


def test_terminal_set() -> None:
    assert {
        OrderStatus.FILLED,
        OrderStatus.CANCELLED,
        OrderStatus.REJECTED,
        OrderStatus.EXPIRED,
        OrderStatus.FAILED,
    } == TERMINAL_STATUSES


def test_illegal_and_terminal_fail_closed() -> None:
    assert not is_legal_transition(OrderStatus.CREATED, OrderStatus.FILLED)
    with pytest.raises(OrderIllegalTransitionError):
        require_legal_transition(OrderStatus.CREATED, OrderStatus.FILLED)
    with pytest.raises(OrderTerminalMutationError):
        require_legal_transition(OrderStatus.FILLED, OrderStatus.CANCELLED)
