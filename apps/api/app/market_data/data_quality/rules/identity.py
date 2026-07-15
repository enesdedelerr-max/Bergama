"""Identity and deterministic key quality rules."""

from __future__ import annotations

from app.market_data.data_quality.models import (
    QualityEvaluationContext,
    QualityRuleId,
    QualityRuleResult,
    QualitySeverity,
)
from app.market_data.data_quality.policy import QualityPolicy
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.keys import build_deduplication_key, build_idempotency_key


def evaluate(
    event: CanonicalMarketEvent,
    policy: QualityPolicy,
    context: QualityEvaluationContext | None,
) -> tuple[QualityRuleResult, ...]:
    return (
        _key_mismatch(event, policy, context),
        _invalid_source(event, policy),
    )


def _key_mismatch(
    event: CanonicalMarketEvent,
    policy: QualityPolicy,
    context: QualityEvaluationContext | None,
) -> QualityRuleResult:
    expected_idempotency = build_idempotency_key(event)
    expected_dedup = build_deduplication_key(event)
    mismatches: list[str] = []
    if context is not None:
        if (
            context.expected_idempotency_key is not None
            and context.expected_idempotency_key != expected_idempotency
        ):
            mismatches.append("idempotency_key")
        if (
            context.expected_deduplication_key is not None
            and context.expected_deduplication_key != expected_dedup
        ):
            mismatches.append("deduplication_key")
    passed = not mismatches
    return QualityRuleResult(
        rule_id=QualityRuleId.IDENTITY_KEY_MISMATCH,
        passed=passed,
        severity=policy.severity_for(
            QualityRuleId.IDENTITY_KEY_MISMATCH,
            QualitySeverity.ERROR if not passed else QualitySeverity.INFO,
        ),
        reason_code="identity_keys_match" if passed else "identity_key_mismatch",
        measured_value=",".join(mismatches) if mismatches else None,
    )


def _invalid_source(event: CanonicalMarketEvent, policy: QualityPolicy) -> QualityRuleResult:
    source = event.source
    issues: list[str] = []
    if not event.instrument.instrument_key.strip():
        issues.append("instrument_key")
    if not source.provider.strip():
        issues.append("source.provider")
    if source.source_symbol and source.source_symbol == event.instrument.instrument_key:
        issues.append("source_symbol_equals_instrument_key")
    passed = not issues
    return QualityRuleResult(
        rule_id=QualityRuleId.IDENTITY_INVALID_SOURCE,
        passed=passed,
        severity=policy.severity_for(
            QualityRuleId.IDENTITY_INVALID_SOURCE,
            QualitySeverity.ERROR if not passed else QualitySeverity.INFO,
        ),
        reason_code="identity_source_valid" if passed else "identity_source_invalid",
        measured_value=",".join(issues) if issues else None,
    )
