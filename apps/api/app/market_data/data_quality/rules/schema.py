"""High-level schema quality rules for already-canonical events."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.market_data.data_quality.models import (
    QualityRuleId,
    QualityRuleResult,
    QualitySeverity,
)
from app.market_data.data_quality.policy import QualityPolicy
from app.market_data.envelope import CanonicalMarketEvent


def evaluate(event: CanonicalMarketEvent, policy: QualityPolicy) -> tuple[QualityRuleResult, ...]:
    return (
        _required_fields(event, policy),
        _invalid_decimal(event, policy),
    )


def _required_fields(event: CanonicalMarketEvent, policy: QualityPolicy) -> QualityRuleResult:
    missing: list[str] = []
    for field_name in ("schema_version", "instrument", "source", "event_type"):
        if getattr(event, field_name, None) is None:
            missing.append(field_name)
    passed = not missing
    return QualityRuleResult(
        rule_id=QualityRuleId.SCHEMA_REQUIRED_FIELD,
        passed=passed,
        severity=policy.severity_for(
            QualityRuleId.SCHEMA_REQUIRED_FIELD,
            QualitySeverity.ERROR if not passed else QualitySeverity.INFO,
        ),
        reason_code="schema_required_fields_present" if passed else "schema_required_field_missing",
        measured_value=",".join(missing) if missing else None,
    )


def _invalid_decimal(event: CanonicalMarketEvent, policy: QualityPolicy) -> QualityRuleResult:
    invalid: list[str] = []
    for field_name, value in event.model_dump(mode="python").items():
        if isinstance(value, Decimal) and not value.is_finite():
            invalid.append(field_name)
        elif isinstance(value, dict):
            invalid.extend(_decimal_paths(value, prefix=field_name))
    passed = not invalid
    return QualityRuleResult(
        rule_id=QualityRuleId.SCHEMA_INVALID_DECIMAL,
        passed=passed,
        severity=policy.severity_for(
            QualityRuleId.SCHEMA_INVALID_DECIMAL,
            QualitySeverity.ERROR if not passed else QualitySeverity.INFO,
        ),
        reason_code="schema_decimals_finite" if passed else "schema_decimal_not_finite",
        measured_value=",".join(invalid[:8]) if invalid else None,
    )


def _decimal_paths(value: dict[str, Any], *, prefix: str) -> list[str]:
    invalid: list[str] = []
    for key, item in value.items():
        path = f"{prefix}.{key}"
        if isinstance(item, Decimal) and not item.is_finite():
            invalid.append(path)
        elif isinstance(item, dict):
            invalid.extend(_decimal_paths(item, prefix=path))
    return invalid
