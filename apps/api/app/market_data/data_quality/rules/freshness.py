"""Freshness and lag quality rules."""

from __future__ import annotations

from datetime import datetime

from app.market_data.data_quality.models import (
    QualityRuleId,
    QualityRuleResult,
    QualitySeverity,
)
from app.market_data.data_quality.policy import QualityPolicy
from app.market_data.envelope import CanonicalMarketEvent


def evaluate(
    event: CanonicalMarketEvent,
    policy: QualityPolicy,
    *,
    evaluated_at: datetime,
) -> tuple[QualityRuleResult, ...]:
    return (
        _threshold_rule(
            rule_id=QualityRuleId.FRESHNESS_EVENT_STALE,
            policy=policy,
            measured_seconds=max(0, int((evaluated_at - event.occurred_at).total_seconds())),
            threshold=policy.freshness_thresholds_by_event_type.get(event.event_type),
            reason_ok="freshness_event_age_within_threshold",
            reason_no_policy="freshness_event_age_no_threshold",
            reason_fail="freshness_event_stale",
        ),
        _threshold_rule(
            rule_id=QualityRuleId.FRESHNESS_INGESTION_LAG,
            policy=policy,
            measured_seconds=max(0, int((event.ingested_at - event.occurred_at).total_seconds())),
            threshold=policy.max_ingestion_lag_by_event_type.get(event.event_type),
            reason_ok="freshness_ingestion_lag_within_threshold",
            reason_no_policy="freshness_ingestion_lag_no_threshold",
            reason_fail="freshness_ingestion_lag_exceeded",
        ),
        _threshold_rule(
            rule_id=QualityRuleId.FRESHNESS_KNOWN_TO_INGESTED_LAG,
            policy=policy,
            measured_seconds=max(0, int((event.ingested_at - event.known_at).total_seconds())),
            threshold=policy.max_known_to_ingested_lag_by_event_type.get(event.event_type),
            reason_ok="freshness_known_lag_within_threshold",
            reason_no_policy="freshness_known_lag_no_threshold",
            reason_fail="freshness_known_lag_exceeded",
        ),
    )


def _threshold_rule(
    *,
    rule_id: QualityRuleId,
    policy: QualityPolicy,
    measured_seconds: int,
    threshold: int | None,
    reason_ok: str,
    reason_no_policy: str,
    reason_fail: str,
) -> QualityRuleResult:
    if threshold is None:
        return QualityRuleResult(
            rule_id=rule_id,
            passed=True,
            severity=policy.severity_for(rule_id, QualitySeverity.INFO),
            reason_code=reason_no_policy,
            measured_value=str(measured_seconds),
            threshold=None,
        )
    passed = measured_seconds <= threshold
    return QualityRuleResult(
        rule_id=rule_id,
        passed=passed,
        severity=policy.severity_for(
            rule_id,
            QualitySeverity.WARNING if not passed else QualitySeverity.INFO,
        ),
        reason_code=reason_ok if passed else reason_fail,
        measured_value=str(measured_seconds),
        threshold=str(threshold),
    )
