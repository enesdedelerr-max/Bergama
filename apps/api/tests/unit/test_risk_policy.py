"""Unit tests for RiskPolicy fingerprinting (#403)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.risk.errors import RiskDecimalError
from app.risk.policy import RiskPolicy
from pydantic import ValidationError
from tests.support.risk_helpers import policy


def test_policy_fingerprint_is_deterministic() -> None:
    first = policy()
    second = policy()
    assert first.policy_fingerprint == second.policy_fingerprint
    assert len(first.policy_fingerprint or "") == 64


def test_policy_fingerprint_ignores_policy_id() -> None:
    a = policy(risk_policy_id="policy-a")
    b = policy(risk_policy_id="policy-b")
    assert a.policy_fingerprint == b.policy_fingerprint


def test_policy_fingerprint_changes_with_limits() -> None:
    a = policy(max_order_notional=Decimal("100000"))
    b = policy(max_order_notional=Decimal("200000"))
    assert a.policy_fingerprint != b.policy_fingerprint


def test_policy_rejects_float_limits() -> None:
    with pytest.raises((RiskDecimalError, ValidationError)):
        policy(max_order_notional=100000.0)  # type: ignore[arg-type]


def test_policy_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        RiskPolicy(
            risk_policy_id="p1",
            risk_policy_version="1.0.0",
            max_order_notional=Decimal("1"),
            max_position_notional=Decimal("1"),
            max_gross_exposure=Decimal("1"),
            max_net_exposure=Decimal("1"),
            max_concentration_ratio=Decimal("1"),
            max_snapshot_age_seconds=1,
            max_mark_age_seconds=1,
            comment="nope",  # type: ignore[call-arg]
        )


def test_policy_rejects_mismatched_fingerprint() -> None:
    with pytest.raises(ValidationError):
        RiskPolicy(
            risk_policy_id="p1",
            risk_policy_version="1.0.0",
            max_order_notional=Decimal("1"),
            max_position_notional=Decimal("1"),
            max_gross_exposure=Decimal("1"),
            max_net_exposure=Decimal("1"),
            max_concentration_ratio=Decimal("1"),
            max_snapshot_age_seconds=1,
            max_mark_age_seconds=1,
            policy_fingerprint="c" * 64,
        )
