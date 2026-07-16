"""Deterministic broker identity hashing (#405)."""

from __future__ import annotations

from app.broker.hashing import (
    build_broker_event_identity,
    build_broker_fill_identity,
    build_submission_identity,
    executable_order_hash,
)
from tests.support.broker_helpers import executable_order_from_submit


def test_submission_identity_is_deterministic() -> None:
    order = executable_order_from_submit()
    h = executable_order_hash(order)
    a = build_submission_identity(
        broker_name="paper",
        broker_account_id="paper-account-1",
        client_order_id=order.client_order_id.value,
        executable_order_hash_value=h,
    )
    b = build_submission_identity(
        broker_name="paper",
        broker_account_id="paper-account-1",
        client_order_id=order.client_order_id.value,
        executable_order_hash_value=h,
    )
    assert a == b
    assert len(a) == 64


def test_broker_event_identity_ignores_timestamps() -> None:
    a = build_broker_event_identity(
        broker_name="paper",
        broker_order_id="bo-1",
        broker_event_type="ACCEPTED",
        broker_sequence=1,
        broker_event_id=None,
    )
    b = build_broker_event_identity(
        broker_name="paper",
        broker_order_id="bo-1",
        broker_event_type="ACCEPTED",
        broker_sequence=1,
        broker_event_id=None,
    )
    assert a == b


def test_fill_identity_prefers_broker_fill_id() -> None:
    a = build_broker_fill_identity(broker_fill_id="bf-1", fill_id=None)
    b = build_broker_fill_identity(broker_fill_id="bf-1", fill_id="ignored")
    assert a == b
