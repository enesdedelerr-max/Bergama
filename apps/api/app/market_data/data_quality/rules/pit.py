"""Point-in-time integrity quality rules."""

from __future__ import annotations

from app.market_data.data_quality.models import (
    QualityRuleId,
    QualityRuleResult,
    QualitySeverity,
)
from app.market_data.data_quality.policy import QualityPolicy
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.timing import validate_point_in_time_order


def evaluate(event: CanonicalMarketEvent, policy: QualityPolicy) -> tuple[QualityRuleResult, ...]:
    try:
        validate_point_in_time_order(
            occurred_at=event.occurred_at,
            effective_at=event.effective_at,
            known_at=event.known_at,
            ingested_at=event.ingested_at,
            quality=event.quality,
        )
    except ValueError as exc:
        return (
            QualityRuleResult(
                rule_id=QualityRuleId.PIT_INVALID_ORDER,
                passed=False,
                severity=policy.severity_for(
                    QualityRuleId.PIT_INVALID_ORDER,
                    QualitySeverity.ERROR,
                ),
                reason_code="pit_invalid_order",
                measured_value=type(exc).__name__,
            ),
        )
    return (
        QualityRuleResult(
            rule_id=QualityRuleId.PIT_INVALID_ORDER,
            passed=True,
            severity=policy.severity_for(
                QualityRuleId.PIT_INVALID_ORDER,
                QualitySeverity.INFO,
            ),
            reason_code="pit_order_valid",
        ),
    )
