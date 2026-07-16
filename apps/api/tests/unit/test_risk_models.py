"""Unit tests for Risk Engine models (#403)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.risk.errors import RiskDecimalError
from app.risk.models import (
    ProposedTradeIntent,
    RiskFinalAction,
    RiskRuleId,
    RiskRuleStatus,
    TradeDirection,
)
from pydantic import ValidationError
from tests.support.risk_helpers import intent


def test_intent_accepts_quantity_delta() -> None:
    value = intent(quantity_delta=Decimal("7"))
    assert value.signed_quantity_delta == Decimal("7")


def test_intent_accepts_quantity_and_direction() -> None:
    buy = intent(quantity_delta=None, quantity=Decimal("3"), direction=TradeDirection.BUY)
    sell = intent(quantity_delta=None, quantity=Decimal("3"), direction=TradeDirection.SELL)
    assert buy.signed_quantity_delta == Decimal("3")
    assert sell.signed_quantity_delta == Decimal("-3")


def test_intent_rejects_both_quantity_representations() -> None:
    payload = intent().model_dump(mode="python")
    payload["quantity"] = Decimal("1")
    payload["direction"] = TradeDirection.BUY
    payload["quantity_delta"] = Decimal("1")
    with pytest.raises(ValidationError):
        ProposedTradeIntent.model_validate(payload)


def test_intent_rejects_float_quantity() -> None:
    with pytest.raises((RiskDecimalError, ValidationError)):
        intent(quantity_delta=1.5)  # type: ignore[arg-type]


def test_intent_rejects_nan_price() -> None:
    with pytest.raises((RiskDecimalError, ValidationError)):
        intent(reference_price=Decimal("NaN"))


def test_intent_rejects_infinity_price() -> None:
    with pytest.raises((RiskDecimalError, ValidationError)):
        intent(reference_price=Decimal("Infinity"))


def test_intent_rejects_zero_quantity() -> None:
    with pytest.raises(ValidationError):
        intent(quantity_delta=Decimal("0"))


def test_intent_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ProposedTradeIntent.model_validate(
            {
                **intent().model_dump(mode="python"),
                "resize_to": "1",
            }
        )


def test_final_action_has_no_reduce() -> None:
    assert set(RiskFinalAction) == {
        RiskFinalAction.APPROVE,
        RiskFinalAction.REJECT,
        RiskFinalAction.HALT,
    }


def test_rule_status_is_not_bool_only() -> None:
    assert set(RiskRuleStatus) == {
        RiskRuleStatus.PASS,
        RiskRuleStatus.FAIL,
        RiskRuleStatus.SKIPPED,
    }


def test_rule_ids_are_closed_taxonomy() -> None:
    assert RiskRuleId.INTENT_INVALID.value == "risk.intent_invalid"
    assert RiskRuleId.KILL_SWITCH.value == "risk.kill_switch"
    assert RiskRuleId.CONCENTRATION_LIMIT.value == "risk.concentration_limit"
