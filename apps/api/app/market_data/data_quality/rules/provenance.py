"""Source provenance and safe metadata quality rules."""

from __future__ import annotations

from collections.abc import Mapping

from app.market_data.data_quality.models import (
    QualityRuleId,
    QualityRuleResult,
    QualitySeverity,
)
from app.market_data.data_quality.policy import QualityPolicy
from app.market_data.envelope import CanonicalMarketEvent

_SENSITIVE_TOKENS = ("password", "secret", "token", "api_key", "apikey", "authorization")
_RAW_PAYLOAD_KEYS = ("raw_body", "raw_payload", "provider_body", "body")


def evaluate(event: CanonicalMarketEvent, policy: QualityPolicy) -> tuple[QualityRuleResult, ...]:
    return (
        _invalid_provenance(event, policy),
        _unsafe_metadata(event, policy),
    )


def _invalid_provenance(event: CanonicalMarketEvent, policy: QualityPolicy) -> QualityRuleResult:
    source = event.source
    issues: list[str] = []
    if not source.provider.strip():
        issues.append("provider")
    if source.source_event_id is None:
        issues.append("source_event_id_missing")
    if source.source_payload_ref and len(source.source_payload_ref) > 512:
        issues.append("payload_ref_unbounded")
    passed = not issues
    return QualityRuleResult(
        rule_id=QualityRuleId.SOURCE_INVALID_PROVENANCE,
        passed=passed,
        severity=policy.severity_for(
            QualityRuleId.SOURCE_INVALID_PROVENANCE,
            QualitySeverity.WARNING if not passed else QualitySeverity.INFO,
        ),
        reason_code="source_provenance_valid" if passed else "source_provenance_invalid",
        measured_value=",".join(issues) if issues else None,
    )


def _unsafe_metadata(event: CanonicalMarketEvent, policy: QualityPolicy) -> QualityRuleResult:
    unsafe = [
        *_unsafe_keys(event.metadata, prefix="metadata"),
        *_unsafe_keys(event.source.extras, prefix="source.extras"),
    ]
    passed = not unsafe
    return QualityRuleResult(
        rule_id=QualityRuleId.SOURCE_UNSAFE_METADATA,
        passed=passed,
        severity=policy.severity_for(
            QualityRuleId.SOURCE_UNSAFE_METADATA,
            QualitySeverity.ERROR if not passed else QualitySeverity.INFO,
        ),
        reason_code="source_metadata_safe" if passed else "source_metadata_unsafe",
        measured_value=",".join(unsafe[:8]) if unsafe else None,
    )


def _unsafe_keys(values: Mapping[str, str], *, prefix: str) -> list[str]:
    unsafe: list[str] = []
    for key, value in values.items():
        lowered_key = key.lower()
        lowered_value = value.lower()
        if any(token in lowered_key for token in _SENSITIVE_TOKENS):
            unsafe.append(f"{prefix}.{key}")
        if any(token in lowered_value for token in ("bearer ", "api_key=", "apikey=", "token=")):
            unsafe.append(f"{prefix}.{key}")
        if any(raw_key == lowered_key for raw_key in _RAW_PAYLOAD_KEYS):
            unsafe.append(f"{prefix}.{key}")
    return unsafe
