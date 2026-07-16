"""Closed Risk Engine rule taxonomy with locked evaluation order."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from app.portfolio.decimal import ZERO, canonical_decimal
from app.risk.context import RiskEvaluationContext
from app.risk.models import (
    RiskRuleId,
    RiskRuleResult,
    RiskRuleStatus,
    RiskSeverity,
)

RuleFn = Callable[[RiskEvaluationContext], tuple[RiskRuleResult, RiskEvaluationContext]]

RULE_ORDER: tuple[RiskRuleId, ...] = (
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

_PRICE_DEPENDENT_RULES: frozenset[RiskRuleId] = frozenset(
    {
        RiskRuleId.GROSS_EXPOSURE_LIMIT,
        RiskRuleId.NET_EXPOSURE_LIMIT,
        RiskRuleId.CONCENTRATION_LIMIT,
    }
)


def evaluate_rules(
    context: RiskEvaluationContext,
) -> tuple[tuple[RiskRuleResult, ...], RiskEvaluationContext]:
    results: list[RiskRuleResult] = []
    current = context
    for rule_id in RULE_ORDER:
        if current.skip_remaining:
            results.append(_skipped(rule_id, reason="short_circuit"))
            continue
        if current.skip_price_dependent and rule_id in _PRICE_DEPENDENT_RULES:
            results.append(_skipped(rule_id, reason="missing_mark"))
            continue
        result, current = _RULE_HANDLERS[rule_id](current)
        results.append(result)
    return tuple(results), current


def _intent_invalid(ctx: RiskEvaluationContext) -> tuple[RiskRuleResult, RiskEvaluationContext]:
    intent = ctx.intent
    snapshot = ctx.snapshot
    policy = ctx.policy
    failures: list[str] = []

    if intent.portfolio_id.value != snapshot.portfolio_id.value:
        failures.append("portfolio_id_mismatch")
    if intent.account_id.value != snapshot.account_id.value:
        failures.append("account_id_mismatch")
    if intent.signed_quantity_delta == ZERO:
        failures.append("zero_quantity")
    if intent.reference_price <= ZERO:
        failures.append("invalid_reference_price")
    allowed = policy.allowed_instruments
    if allowed is not None and intent.instrument_id.instrument_key not in allowed:
        failures.append("instrument_not_allowed")

    if failures:
        result = RiskRuleResult(
            rule_id=RiskRuleId.INTENT_INVALID,
            status=RiskRuleStatus.FAIL,
            severity=RiskSeverity.ERROR,
            observed_value=",".join(failures),
            limit_value="valid_intent",
            safe_metadata={"reason": failures[0]},
        )
        return result, replace(ctx, skip_remaining=True)
    return (
        RiskRuleResult(
            rule_id=RiskRuleId.INTENT_INVALID,
            status=RiskRuleStatus.PASS,
            severity=RiskSeverity.INFO,
            observed_value="valid",
            limit_value="valid_intent",
        ),
        ctx,
    )


def _policy_currency(ctx: RiskEvaluationContext) -> tuple[RiskRuleResult, RiskEvaluationContext]:
    intent_ccy = ctx.intent.currency
    policy_ccy = ctx.policy.base_currency
    snapshot_ccy = ctx.snapshot.base_currency
    ok = intent_ccy == policy_ccy == snapshot_ccy
    if not ok:
        return (
            RiskRuleResult(
                rule_id=RiskRuleId.POLICY_CURRENCY_MISMATCH,
                status=RiskRuleStatus.FAIL,
                severity=RiskSeverity.ERROR,
                observed_value=f"{intent_ccy}/{snapshot_ccy}/{policy_ccy}",
                limit_value=policy_ccy,
            ),
            ctx,
        )
    return (
        RiskRuleResult(
            rule_id=RiskRuleId.POLICY_CURRENCY_MISMATCH,
            status=RiskRuleStatus.PASS,
            severity=RiskSeverity.INFO,
            observed_value=intent_ccy,
            limit_value=policy_ccy,
        ),
        ctx,
    )


def _portfolio_version(ctx: RiskEvaluationContext) -> tuple[RiskRuleResult, RiskEvaluationContext]:
    expected = ctx.intent.expected_portfolio_version
    actual = ctx.snapshot.portfolio_version
    if expected != actual:
        return (
            RiskRuleResult(
                rule_id=RiskRuleId.PORTFOLIO_VERSION_MISMATCH,
                status=RiskRuleStatus.FAIL,
                severity=RiskSeverity.ERROR,
                observed_value=str(actual),
                limit_value=str(expected),
            ),
            ctx,
        )
    return (
        RiskRuleResult(
            rule_id=RiskRuleId.PORTFOLIO_VERSION_MISMATCH,
            status=RiskRuleStatus.PASS,
            severity=RiskSeverity.INFO,
            observed_value=str(actual),
            limit_value=str(expected),
        ),
        ctx,
    )


def _kill_switch(ctx: RiskEvaluationContext) -> tuple[RiskRuleResult, RiskEvaluationContext]:
    if ctx.policy.kill_switch_enabled:
        result = RiskRuleResult(
            rule_id=RiskRuleId.KILL_SWITCH,
            status=RiskRuleStatus.FAIL,
            severity=RiskSeverity.CRITICAL,
            observed_value="enabled",
            limit_value="disabled",
        )
        return result, replace(ctx, skip_remaining=True, halt=True)
    return (
        RiskRuleResult(
            rule_id=RiskRuleId.KILL_SWITCH,
            status=RiskRuleStatus.PASS,
            severity=RiskSeverity.INFO,
            observed_value="disabled",
            limit_value="disabled",
        ),
        ctx,
    )


def _snapshot_stale(ctx: RiskEvaluationContext) -> tuple[RiskRuleResult, RiskEvaluationContext]:
    age = (ctx.evaluated_at - ctx.snapshot.snapshot_at).total_seconds()
    limit = ctx.policy.max_snapshot_age_seconds
    if age < 0 or age > limit:
        return (
            RiskRuleResult(
                rule_id=RiskRuleId.SNAPSHOT_STALE,
                status=RiskRuleStatus.FAIL,
                severity=RiskSeverity.ERROR,
                observed_value="stale",
                limit_value=str(limit),
                safe_metadata={"age_seconds": str(int(age))},
            ),
            ctx,
        )
    return (
        RiskRuleResult(
            rule_id=RiskRuleId.SNAPSHOT_STALE,
            status=RiskRuleStatus.PASS,
            severity=RiskSeverity.INFO,
            observed_value="fresh",
            limit_value=str(limit),
            safe_metadata={"age_seconds": str(int(age))},
        ),
        ctx,
    )


def _mark_stale(ctx: RiskEvaluationContext) -> tuple[RiskRuleResult, RiskEvaluationContext]:
    if ctx.current_position is None:
        return (
            RiskRuleResult(
                rule_id=RiskRuleId.MARK_STALE,
                status=RiskRuleStatus.PASS,
                severity=RiskSeverity.INFO,
                observed_value="no_position",
                limit_value=str(ctx.policy.max_mark_age_seconds),
            ),
            ctx,
        )
    if ctx.mark_missing or ctx.mark_at is None:
        result = RiskRuleResult(
            rule_id=RiskRuleId.MARK_STALE,
            status=RiskRuleStatus.FAIL,
            severity=RiskSeverity.ERROR,
            observed_value="missing_mark",
            limit_value=str(ctx.policy.max_mark_age_seconds),
        )
        return result, replace(ctx, skip_price_dependent=True)
    age = (ctx.evaluated_at - ctx.mark_at).total_seconds()
    limit = ctx.policy.max_mark_age_seconds
    if age < 0 or age > limit:
        result = RiskRuleResult(
            rule_id=RiskRuleId.MARK_STALE,
            status=RiskRuleStatus.FAIL,
            severity=RiskSeverity.ERROR,
            observed_value="stale",
            limit_value=str(limit),
            safe_metadata={"age_seconds": str(int(age))},
        )
        return result, replace(ctx, skip_price_dependent=True)
    return (
        RiskRuleResult(
            rule_id=RiskRuleId.MARK_STALE,
            status=RiskRuleStatus.PASS,
            severity=RiskSeverity.INFO,
            observed_value="fresh",
            limit_value=str(limit),
            safe_metadata={"age_seconds": str(int(age))},
        ),
        ctx,
    )


def _shorting_disabled(ctx: RiskEvaluationContext) -> tuple[RiskRuleResult, RiskEvaluationContext]:
    short_limit = "shorts_allowed" if ctx.policy.allow_short_positions else "non_negative"
    if ctx.policy.allow_short_positions or ctx.resulting_quantity >= ZERO:
        return (
            RiskRuleResult(
                rule_id=RiskRuleId.SHORTING_DISABLED,
                status=RiskRuleStatus.PASS,
                severity=RiskSeverity.INFO,
                observed_value=canonical_decimal(ctx.resulting_quantity),
                limit_value=short_limit,
            ),
            ctx,
        )
    return (
        RiskRuleResult(
            rule_id=RiskRuleId.SHORTING_DISABLED,
            status=RiskRuleStatus.FAIL,
            severity=RiskSeverity.ERROR,
            observed_value=canonical_decimal(ctx.resulting_quantity),
            limit_value="non_negative",
        ),
        ctx,
    )


def _order_notional(ctx: RiskEvaluationContext) -> tuple[RiskRuleResult, RiskEvaluationContext]:
    limit = ctx.policy.max_order_notional
    observed = ctx.order_notional
    status = RiskRuleStatus.PASS if observed <= limit else RiskRuleStatus.FAIL
    return (
        RiskRuleResult(
            rule_id=RiskRuleId.ORDER_NOTIONAL_LIMIT,
            status=status,
            severity=RiskSeverity.INFO if status is RiskRuleStatus.PASS else RiskSeverity.ERROR,
            observed_value=canonical_decimal(observed),
            limit_value=canonical_decimal(limit),
        ),
        ctx,
    )


def _position_notional(ctx: RiskEvaluationContext) -> tuple[RiskRuleResult, RiskEvaluationContext]:
    limit = ctx.policy.max_position_notional
    observed = ctx.resulting_position_notional
    status = RiskRuleStatus.PASS if observed <= limit else RiskRuleStatus.FAIL
    return (
        RiskRuleResult(
            rule_id=RiskRuleId.POSITION_NOTIONAL_LIMIT,
            status=status,
            severity=RiskSeverity.INFO if status is RiskRuleStatus.PASS else RiskSeverity.ERROR,
            observed_value=canonical_decimal(observed),
            limit_value=canonical_decimal(limit),
        ),
        ctx,
    )


def _gross_exposure(ctx: RiskEvaluationContext) -> tuple[RiskRuleResult, RiskEvaluationContext]:
    limit = ctx.policy.max_gross_exposure
    observed = ctx.resulting_gross_exposure
    status = RiskRuleStatus.PASS if observed <= limit else RiskRuleStatus.FAIL
    return (
        RiskRuleResult(
            rule_id=RiskRuleId.GROSS_EXPOSURE_LIMIT,
            status=status,
            severity=RiskSeverity.INFO if status is RiskRuleStatus.PASS else RiskSeverity.ERROR,
            observed_value=canonical_decimal(observed),
            limit_value=canonical_decimal(limit),
        ),
        ctx,
    )


def _net_exposure(ctx: RiskEvaluationContext) -> tuple[RiskRuleResult, RiskEvaluationContext]:
    limit = ctx.policy.max_net_exposure
    observed = abs(ctx.resulting_net_exposure)
    status = RiskRuleStatus.PASS if observed <= limit else RiskRuleStatus.FAIL
    return (
        RiskRuleResult(
            rule_id=RiskRuleId.NET_EXPOSURE_LIMIT,
            status=status,
            severity=RiskSeverity.INFO if status is RiskRuleStatus.PASS else RiskSeverity.ERROR,
            observed_value=canonical_decimal(observed),
            limit_value=canonical_decimal(limit),
        ),
        ctx,
    )


def _concentration(ctx: RiskEvaluationContext) -> tuple[RiskRuleResult, RiskEvaluationContext]:
    limit = ctx.policy.max_concentration_ratio
    if ctx.concentration_ratio is None:
        return (
            RiskRuleResult(
                rule_id=RiskRuleId.CONCENTRATION_LIMIT,
                status=RiskRuleStatus.FAIL,
                severity=RiskSeverity.ERROR,
                observed_value="zero_gross",
                limit_value=canonical_decimal(limit),
                safe_metadata={"reason": "zero_denominator"},
            ),
            ctx,
        )
    observed = ctx.concentration_ratio
    status = RiskRuleStatus.PASS if observed <= limit else RiskRuleStatus.FAIL
    return (
        RiskRuleResult(
            rule_id=RiskRuleId.CONCENTRATION_LIMIT,
            status=status,
            severity=RiskSeverity.INFO if status is RiskRuleStatus.PASS else RiskSeverity.ERROR,
            observed_value=canonical_decimal(observed),
            limit_value=canonical_decimal(limit),
        ),
        ctx,
    )


def _skipped(rule_id: RiskRuleId, *, reason: str) -> RiskRuleResult:
    return RiskRuleResult(
        rule_id=rule_id,
        status=RiskRuleStatus.SKIPPED,
        severity=RiskSeverity.INFO,
        observed_value=None,
        limit_value=None,
        safe_metadata={"reason": reason},
    )


_RULE_HANDLERS: dict[RiskRuleId, RuleFn] = {
    RiskRuleId.INTENT_INVALID: _intent_invalid,
    RiskRuleId.POLICY_CURRENCY_MISMATCH: _policy_currency,
    RiskRuleId.PORTFOLIO_VERSION_MISMATCH: _portfolio_version,
    RiskRuleId.KILL_SWITCH: _kill_switch,
    RiskRuleId.SNAPSHOT_STALE: _snapshot_stale,
    RiskRuleId.MARK_STALE: _mark_stale,
    RiskRuleId.SHORTING_DISABLED: _shorting_disabled,
    RiskRuleId.ORDER_NOTIONAL_LIMIT: _order_notional,
    RiskRuleId.POSITION_NOTIONAL_LIMIT: _position_notional,
    RiskRuleId.GROSS_EXPOSURE_LIMIT: _gross_exposure,
    RiskRuleId.NET_EXPOSURE_LIMIT: _net_exposure,
    RiskRuleId.CONCENTRATION_LIMIT: _concentration,
}
