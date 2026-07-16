"""BrokerCapabilities fingerprint and validate-before-submit (#405)."""

from __future__ import annotations

import pytest
from app.broker.capabilities import BrokerCapabilities, paper_broker_capabilities
from app.broker.errors import BrokerCapabilityMismatchError
from app.broker.hashing import build_capability_fingerprint
from app.broker.reference import validate_before_submit
from app.orders.models import OrderType, TimeInForce
from tests.support.broker_helpers import executable_order_from_submit
from tests.support.order_helpers import submit_cmd


def test_capabilities_are_frozen_with_fingerprint() -> None:
    caps = paper_broker_capabilities()
    assert BrokerCapabilities.model_config.get("frozen") is True
    assert caps.capability_fingerprint is not None
    assert len(caps.capability_fingerprint) == 64
    assert caps.capability_fingerprint == build_capability_fingerprint(caps.canonical_dict())


def test_capability_fingerprint_changes_when_flags_change() -> None:
    a = BrokerCapabilities(supports_cancel=True)
    b = BrokerCapabilities(supports_cancel=False)
    assert a.capability_fingerprint != b.capability_fingerprint


def test_validate_before_submit_rejects_unsupported_tif() -> None:
    order = executable_order_from_submit(
        submit_cmd(client_order_id="caps-tif", time_in_force=TimeInForce.GTC)
    )
    caps = BrokerCapabilities(supported_time_in_force=(TimeInForce.DAY,))
    with pytest.raises(BrokerCapabilityMismatchError, match="time_in_force"):
        validate_before_submit(order, caps)


def test_validate_before_submit_rejects_unsupported_order_type() -> None:
    order = executable_order_from_submit(
        submit_cmd(
            client_order_id="caps-type",
            order_type=OrderType.LIMIT,
            limit_price="100.00",
        )
    )
    caps = BrokerCapabilities(supported_order_types=(OrderType.MARKET,))
    with pytest.raises(BrokerCapabilityMismatchError, match="order_type"):
        validate_before_submit(order, caps)
