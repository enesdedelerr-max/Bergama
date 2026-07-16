"""Unit tests for Risk Engine rule ordering and short-circuit (#403)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from app.risk.models import RiskFinalAction, RiskRuleId, RiskRuleStatus
from app.risk.rules import RULE_ORDER
from tests.support.risk_helpers import T0, empty_snapshot, engine, intent, marked_snapshot, policy


def test_rule_order_is_locked() -> None:
    assert RULE_ORDER == (
        RiskRuleId.INTENT_INVALID,
        RiskRuleId.POLICY_CURRENCY_MISMATCH,
        RiskRuleId.PORTFOLIO_VERSION_MISMATCH,
        RiskRuleId.KILL_SWITCH,
        RiskRuleId.SNAPSHOT_STALE,
        RiskRuleId.MARK_STALE,
        RiskRuleId.SHORTING_DISABLED,
        RiskRuleId.ORDER_NOTIONAL_LIMIT,
        RiskRuleId.POSITION_NOTIONAL_LIMIT,
        RiskRuleId.GROSS_EXPOSURE_LIMIT,
        RiskRuleId.NET_EXPOSURE_LIMIT,
        RiskRuleId.CONCENTRATION_LIMIT,
    )


def _by_id(assessment):  # type: ignore[no-untyped-def]
    return {result.rule_id: result for result in assessment.rule_results}


def test_intent_invalid_short_circuits_remaining() -> None:
    assessment = engine().evaluate(
        intent=intent(expected_portfolio_version=1),
        snapshot=empty_snapshot(version=1),
        policy=policy(allowed_instruments=("bergama:equity:us:msft",)),
        evaluated_at=T0 + timedelta(seconds=1),
    )
    results = _by_id(assessment)
    assert results[RiskRuleId.INTENT_INVALID].status is RiskRuleStatus.FAIL
    assert results[RiskRuleId.KILL_SWITCH].status is RiskRuleStatus.SKIPPED
    assert results[RiskRuleId.CONCENTRATION_LIMIT].status is RiskRuleStatus.SKIPPED
    assert assessment.final_action is RiskFinalAction.REJECT


def test_kill_switch_halts_and_skips_remaining() -> None:
    assessment = engine().evaluate(
        intent=intent(expected_portfolio_version=1),
        snapshot=empty_snapshot(version=1),
        policy=policy(kill_switch_enabled=True),
        evaluated_at=T0 + timedelta(seconds=1),
    )
    results = _by_id(assessment)
    assert results[RiskRuleId.KILL_SWITCH].status is RiskRuleStatus.FAIL
    assert results[RiskRuleId.SNAPSHOT_STALE].status is RiskRuleStatus.SKIPPED
    assert assessment.final_action is RiskFinalAction.HALT


def test_version_mismatch_rejects_not_halt() -> None:
    assessment = engine().evaluate(
        intent=intent(expected_portfolio_version=9),
        snapshot=empty_snapshot(version=1),
        policy=policy(),
        evaluated_at=T0 + timedelta(seconds=1),
    )
    assert _by_id(assessment)[RiskRuleId.PORTFOLIO_VERSION_MISMATCH].status is RiskRuleStatus.FAIL
    assert assessment.final_action is RiskFinalAction.REJECT


def test_snapshot_stale_rejects() -> None:
    assessment = engine().evaluate(
        intent=intent(expected_portfolio_version=1),
        snapshot=empty_snapshot(version=1, snapshot_at=T0 - timedelta(seconds=1000)),
        policy=policy(max_snapshot_age_seconds=60),
        evaluated_at=T0,
    )
    assert _by_id(assessment)[RiskRuleId.SNAPSHOT_STALE].status is RiskRuleStatus.FAIL
    assert assessment.final_action is RiskFinalAction.REJECT


def test_mark_stale_skips_price_dependent_rules() -> None:
    snapshot = marked_snapshot(mark_at=T0 - timedelta(seconds=1000), version=3)
    assessment = engine().evaluate(
        intent=intent(expected_portfolio_version=3, quantity_delta=Decimal("1")),
        snapshot=snapshot,
        policy=policy(max_mark_age_seconds=60),
        evaluated_at=T0,
    )
    results = _by_id(assessment)
    assert results[RiskRuleId.MARK_STALE].status is RiskRuleStatus.FAIL
    assert results[RiskRuleId.ORDER_NOTIONAL_LIMIT].status is RiskRuleStatus.PASS
    assert results[RiskRuleId.GROSS_EXPOSURE_LIMIT].status is RiskRuleStatus.SKIPPED
    assert results[RiskRuleId.NET_EXPOSURE_LIMIT].status is RiskRuleStatus.SKIPPED
    assert results[RiskRuleId.CONCENTRATION_LIMIT].status is RiskRuleStatus.SKIPPED
    assert assessment.final_action is RiskFinalAction.REJECT


def test_currency_mismatch_rejects() -> None:
    assessment = engine().evaluate(
        intent=intent(expected_portfolio_version=1, currency="EUR"),
        snapshot=empty_snapshot(version=1),
        policy=policy(base_currency="USD"),
        evaluated_at=T0 + timedelta(seconds=1),
    )
    assert _by_id(assessment)[RiskRuleId.POLICY_CURRENCY_MISMATCH].status is RiskRuleStatus.FAIL
    assert assessment.final_action is RiskFinalAction.REJECT


def test_shorting_disabled_rejects() -> None:
    assessment = engine().evaluate(
        intent=intent(expected_portfolio_version=3, quantity_delta=Decimal("-20")),
        snapshot=marked_snapshot(quantity=Decimal("5"), version=3),
        policy=policy(allow_short_positions=False),
        evaluated_at=T0 + timedelta(seconds=1),
    )
    assert _by_id(assessment)[RiskRuleId.SHORTING_DISABLED].status is RiskRuleStatus.FAIL
    assert assessment.final_action is RiskFinalAction.REJECT


def test_order_notional_limit() -> None:
    assessment = engine().evaluate(
        intent=intent(
            expected_portfolio_version=1,
            quantity_delta=Decimal("10"),
            reference_price=Decimal("100"),
        ),
        snapshot=empty_snapshot(version=1),
        policy=policy(max_order_notional=Decimal("500")),
        evaluated_at=T0 + timedelta(seconds=1),
    )
    assert _by_id(assessment)[RiskRuleId.ORDER_NOTIONAL_LIMIT].status is RiskRuleStatus.FAIL
    assert assessment.final_action is RiskFinalAction.REJECT


def test_position_notional_limit() -> None:
    assessment = engine().evaluate(
        intent=intent(
            expected_portfolio_version=3,
            quantity_delta=Decimal("10"),
            reference_price=Decimal("100"),
        ),
        snapshot=marked_snapshot(quantity=Decimal("10"), mark_price=Decimal("100"), version=3),
        policy=policy(max_position_notional=Decimal("1500")),
        evaluated_at=T0 + timedelta(seconds=1),
    )
    assert _by_id(assessment)[RiskRuleId.POSITION_NOTIONAL_LIMIT].status is RiskRuleStatus.FAIL


def test_gross_net_concentration_limits() -> None:
    assessment = engine().evaluate(
        intent=intent(
            expected_portfolio_version=3,
            quantity_delta=Decimal("100"),
            reference_price=Decimal("100"),
        ),
        snapshot=marked_snapshot(quantity=Decimal("10"), mark_price=Decimal("100"), version=3),
        policy=policy(
            max_order_notional=Decimal("1000000"),
            max_position_notional=Decimal("1000000"),
            max_gross_exposure=Decimal("5000"),
            max_net_exposure=Decimal("5000"),
            max_concentration_ratio=Decimal("0.10"),
        ),
        evaluated_at=T0 + timedelta(seconds=1),
    )
    results = _by_id(assessment)
    assert results[RiskRuleId.GROSS_EXPOSURE_LIMIT].status is RiskRuleStatus.FAIL
    assert results[RiskRuleId.NET_EXPOSURE_LIMIT].status is RiskRuleStatus.FAIL
    assert results[RiskRuleId.CONCENTRATION_LIMIT].status is RiskRuleStatus.FAIL
