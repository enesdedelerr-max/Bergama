"""Provider-independent data-quality engine and service (#310)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from inspect import isawaitable

from app.core.clock import Clock
from app.market_data.data_quality.errors import DataQualityQuarantineUnavailableError
from app.market_data.data_quality.metrics import QualityMetrics
from app.market_data.data_quality.models import (
    QualityAction,
    QualityAssessment,
    QualityEvaluationContext,
    QualityOperationalOutcomeType,
    QualityRuleId,
    QualityRuleResult,
    QualitySeverity,
    QualityStatus,
)
from app.market_data.data_quality.policy import QualityPolicy
from app.market_data.data_quality.quarantine import QuarantinePort, QuarantineResult
from app.market_data.data_quality.rules import (
    completeness,
    freshness,
    identity,
    pit,
    provenance,
    schema,
    values,
)
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.keys import build_idempotency_key
from app.schemas.health import DependencyHealthResult, DependencyHealthStatus

_SEVERITY_RANK: dict[QualitySeverity, int] = {
    QualitySeverity.INFO: 0,
    QualitySeverity.WARNING: 1,
    QualitySeverity.ERROR: 2,
    QualitySeverity.CRITICAL: 3,
}


@dataclass(slots=True)
class QualityRuleEngine:
    """Evaluate closed-registry quality rules for valid canonical events."""

    policy: QualityPolicy
    clock: Clock

    def evaluate(
        self,
        event: CanonicalMarketEvent,
        *,
        context: QualityEvaluationContext | None = None,
    ) -> QualityAssessment:
        evaluated_at = self.clock.now()
        all_results = (
            *schema.evaluate(event, self.policy),
            *pit.evaluate(event, self.policy),
            *identity.evaluate(event, self.policy, context),
            *freshness.evaluate(event, self.policy, evaluated_at=evaluated_at),
            *completeness.evaluate(event, self.policy),
            *values.evaluate(event, self.policy),
            *provenance.evaluate(event, self.policy),
            *self._duplication_results(context),
            *self._operational_results(context),
        )
        active = set(self.policy.active_rule_ids())
        results = tuple(
            sorted(
                (result for result in all_results if result.rule_id in active),
                key=lambda result: result.rule_id.value,
            )
        )
        highest = _highest_severity(results)
        status = _overall_status(results, highest)
        action = self.policy.resolve_action(status=status, highest_severity=highest)
        policy_fingerprint = self.policy.fingerprint()
        idempotency_key = build_idempotency_key(event)
        assessment_id = _assessment_id(
            event_type=event.event_type.value,
            instrument_key=event.instrument.instrument_key,
            idempotency_key=idempotency_key,
            evaluated_at=evaluated_at,
            policy_fingerprint=policy_fingerprint,
            results=results,
        )
        return QualityAssessment(
            assessment_id=assessment_id,
            event_type=event.event_type.value,
            instrument_key=event.instrument.instrument_key,
            idempotency_key=idempotency_key,
            evaluated_at=evaluated_at,
            overall_status=status,
            highest_severity=highest,
            recommended_action=action,
            rule_results=results,
            existing_quality_flags=event.quality,
            policy_fingerprint=policy_fingerprint,
            safe_metadata={"source_provider": event.source.provider[:64]},
        )

    def _duplication_results(
        self,
        context: QualityEvaluationContext | None,
    ) -> tuple[QualityRuleResult, ...]:
        duplicate = bool(context and context.duplicate_observed)
        return (
            QualityRuleResult(
                rule_id=QualityRuleId.DUPLICATION_DUPLICATE_OBSERVATION,
                passed=not duplicate,
                severity=self.policy.severity_for(
                    QualityRuleId.DUPLICATION_DUPLICATE_OBSERVATION,
                    QualitySeverity.WARNING if duplicate else QualitySeverity.INFO,
                ),
                reason_code="duplication_not_observed" if not duplicate else "duplication_observed",
            ),
        )

    def _operational_results(
        self,
        context: QualityEvaluationContext | None,
    ) -> tuple[QualityRuleResult, ...]:
        if context is None or context.operational_rule_id is None:
            return tuple(
                QualityRuleResult(
                    rule_id=rule_id,
                    passed=True,
                    severity=self.policy.severity_for(rule_id, QualitySeverity.INFO),
                    reason_code=f"{rule_id.value.replace('.', '_')}_not_observed",
                )
                for rule_id in (
                    QualityRuleId.OPERATIONAL_PUBLISH_FAILED,
                    QualityRuleId.OPERATIONAL_WRITER_FAILED,
                    QualityRuleId.OPERATIONAL_CHECKPOINT_FAILED,
                    QualityRuleId.OPERATIONAL_ADMISSION_OVERFLOW,
                )
            )
        rule_id = context.operational_rule_id
        return (
            QualityRuleResult(
                rule_id=rule_id,
                passed=False,
                severity=self.policy.severity_for(rule_id, QualitySeverity.ERROR),
                reason_code=context.operational_reason_code or "operational_failure",
                safe_metadata=context.safe_metadata,
            ),
        )


@dataclass(slots=True)
class DataQualityService:
    """Container-owned quality subsystem. No provider calls or background work."""

    policy: QualityPolicy
    clock: Clock
    metrics: QualityMetrics = field(default_factory=QualityMetrics)
    quarantine_port: QuarantinePort | None = None
    enabled: bool = True
    required: bool = False
    readiness_fail_on_critical_halt: bool = False
    _engine: QualityRuleEngine = field(init=False, repr=False)
    _critical_halt_active: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        self._engine = QualityRuleEngine(policy=self.policy, clock=self.clock)

    @property
    def critical_halt_active(self) -> bool:
        return self._critical_halt_active

    def evaluate(
        self,
        event: CanonicalMarketEvent,
        *,
        context: QualityEvaluationContext | None = None,
    ) -> QualityAssessment:
        assessment = self._engine.evaluate(event, context=context)
        self.metrics.record_assessment(assessment)
        if assessment.recommended_action is QualityAction.HALT_PIPELINE:
            self._critical_halt_active = True
        return assessment

    async def quarantine(
        self,
        event: CanonicalMarketEvent,
        *,
        assessment: QualityAssessment,
        correlation_id: str,
    ) -> QuarantineResult:
        if self.quarantine_port is None:
            raise DataQualityQuarantineUnavailableError(detail="quarantine port is not configured")
        result = await self.quarantine_port.quarantine(
            event,
            assessment=assessment,
            correlation_id=correlation_id,
        )
        self.metrics.record_quarantine(result.succeeded)
        return result

    def record_operational_outcome(
        self,
        outcome_type: QualityOperationalOutcomeType,
        *,
        reason_code: str,
        safe_metadata: dict[str, object] | None = None,
    ) -> None:
        """Record non-event operational failures without manufacturing market events."""
        del reason_code, safe_metadata
        self.metrics.record_operational_outcome(outcome_type)

    def health_check(self) -> DependencyHealthResult:
        if not self.enabled:
            return DependencyHealthResult(
                name="data_quality",
                status=DependencyHealthStatus.SKIPPED,
                required=self.required,
                latency_ms=0.0,
                message="data quality disabled",
            )
        if self._critical_halt_active and self.readiness_fail_on_critical_halt:
            return DependencyHealthResult(
                name="data_quality",
                status=DependencyHealthStatus.FAIL,
                required=self.required,
                latency_ms=0.0,
                message="critical quality halt active",
                error_code="data_quality.critical_halt",
            )
        return DependencyHealthResult(
            name="data_quality",
            status=DependencyHealthStatus.PASS,
            required=self.required,
            latency_ms=0.0,
            message="data quality initialized",
        )

    async def aclose(self) -> None:
        close = getattr(self.quarantine_port, "aclose", None)
        if callable(close):
            result = close()
            if isawaitable(result):
                await result
        self.metrics.clear()


@dataclass(slots=True)
class DataQualityHealthCheck:
    service: DataQualityService
    timeout_seconds: float
    name: str = "data_quality"

    @property
    def required(self) -> bool:
        return self.service.required

    async def check(self) -> DependencyHealthResult:
        return self.service.health_check()


def _highest_severity(results: tuple[QualityRuleResult, ...]) -> QualitySeverity:
    failed = [result.severity for result in results if not result.passed]
    if not failed:
        return QualitySeverity.INFO
    return max(failed, key=lambda severity: _SEVERITY_RANK[severity])


def _overall_status(
    results: tuple[QualityRuleResult, ...],
    highest: QualitySeverity,
) -> QualityStatus:
    if all(result.passed for result in results):
        return QualityStatus.PASSED
    if highest is QualitySeverity.CRITICAL:
        return QualityStatus.CRITICAL
    if highest is QualitySeverity.ERROR:
        return QualityStatus.FAILED
    return QualityStatus.DEGRADED


def _assessment_id(
    *,
    event_type: str,
    instrument_key: str,
    idempotency_key: str,
    evaluated_at: datetime,
    policy_fingerprint: str,
    results: tuple[QualityRuleResult, ...],
) -> str:
    payload = {
        "event_type": event_type,
        "instrument_key": instrument_key,
        "idempotency_key": idempotency_key,
        "evaluated_at": evaluated_at.isoformat().replace("+00:00", "Z"),
        "policy_fingerprint": policy_fingerprint,
        "results": [result.model_dump(mode="json") for result in results],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
