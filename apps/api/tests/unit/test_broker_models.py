"""Unit tests for broker models and outcomes (#405)."""

from __future__ import annotations

import pytest
from app.broker.models import BrokerSubmissionResult, SubmitExecutableOrder
from app.broker.outcomes import BrokerCommandOutcome
from app.orders.models import ExecutableOrder
from pydantic import ValidationError
from tests.support.broker_helpers import executable_order_from_submit, submit_executable


def test_executable_order_remains_frozen() -> None:
    order = executable_order_from_submit()
    assert ExecutableOrder.model_config.get("frozen") is True
    with pytest.raises(ValidationError):
        order.quantity = order.quantity  # type: ignore[misc]


def test_submit_command_is_frozen() -> None:
    cmd = submit_executable()
    assert SubmitExecutableOrder.model_config.get("frozen") is True
    with pytest.raises(ValidationError):
        cmd.idempotency_key = "x"  # type: ignore[misc]


def test_submission_result_outcomes_are_exclusive_enum() -> None:
    values = {o.value for o in BrokerCommandOutcome}
    assert values == {
        "ACKNOWLEDGED",
        "REJECTED",
        "FAILED_BEFORE_SEND",
        "OUTCOME_UNKNOWN",
        "RECONCILIATION_REQUIRED",
    }


def test_submission_result_requires_submission_identity() -> None:
    order = executable_order_from_submit()
    result = BrokerSubmissionResult(
        outcome=BrokerCommandOutcome.ACKNOWLEDGED,
        submission_identity="a" * 64,
        broker_order_id="b1",
        correlation_id=order.correlation_id,
    )
    assert result.outcome is BrokerCommandOutcome.ACKNOWLEDGED
    assert result.fill_events == ()
