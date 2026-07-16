"""Reference RiskPolicy builders for contract and unit tests."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.risk.policy import RiskPolicy


def reference_risk_policy(
    *,
    risk_policy_id: str = "risk-policy-reference",
    risk_policy_version: str = "1.0.0",
    kill_switch_enabled: bool = False,
    allow_short_positions: bool = False,
    max_order_notional: Decimal | str = Decimal("100000"),
    max_position_notional: Decimal | str = Decimal("250000"),
    max_gross_exposure: Decimal | str = Decimal("500000"),
    max_net_exposure: Decimal | str = Decimal("500000"),
    max_concentration_ratio: Decimal | str = Decimal("1"),
    max_snapshot_age_seconds: int = 300,
    max_mark_age_seconds: int = 300,
    allowed_instruments: tuple[str, ...] | None = None,
    base_currency: str = "USD",
) -> RiskPolicy:
    payload: dict[str, Any] = {
        "risk_policy_id": risk_policy_id,
        "risk_policy_version": risk_policy_version,
        "base_currency": base_currency,
        "kill_switch_enabled": kill_switch_enabled,
        "allow_short_positions": allow_short_positions,
        "max_order_notional": max_order_notional,
        "max_position_notional": max_position_notional,
        "max_gross_exposure": max_gross_exposure,
        "max_net_exposure": max_net_exposure,
        "max_concentration_ratio": max_concentration_ratio,
        "max_snapshot_age_seconds": max_snapshot_age_seconds,
        "max_mark_age_seconds": max_mark_age_seconds,
        "allowed_instruments": allowed_instruments,
    }
    return RiskPolicy.model_validate(payload)
