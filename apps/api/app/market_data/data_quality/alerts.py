"""Alert-ready signal models and deterministic generation (#310)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.clock import Clock
from app.market_data.data_quality.metrics import QualityMetrics
from app.market_data.data_quality.models import QualitySeverity, validate_safe_metadata
from app.market_data.data_quality.policy import QualityPolicy
from app.market_data.timing import require_utc_aware


class AlertSignalType(StrEnum):
    CRITICAL_RULE_FAILURE = "critical_rule_failure"
    SUSTAINED_REJECTION_RATE = "sustained_rejection_rate"
    SUSTAINED_STALE_RATE = "sustained_stale_rate"
    REPEATED_OPERATIONAL_FAILURE = "repeated_operational_failure"
    FRESHNESS_BREACH = "freshness_breach"
    REPEATED_PUBLISH_FAILURE = "repeated_publish_failure"
    WRITER_FAILURE = "writer_failure"
    CHECKPOINT_FAILURE = "checkpoint_failure"
    REPLAY_FAILURE = "replay_failure"
    BACKFILL_FAILURE = "backfill_failure"
    ADMISSION_OVERFLOW = "admission_overflow"


class AlertSignal(BaseModel):
    """Notification-free alert-ready signal."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    signal_id: str = Field(min_length=1, max_length=128)
    signal_type: AlertSignalType
    severity: QualitySeverity
    first_seen_at: datetime
    last_seen_at: datetime
    count: int = Field(ge=1)
    dimensions: dict[str, str] = Field(default_factory=dict)
    reason_code: str = Field(min_length=1, max_length=96)

    @field_validator("first_seen_at", "last_seen_at")
    @classmethod
    def utc_times(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="alert_time")

    @field_validator("dimensions")
    @classmethod
    def validate_dimensions(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_safe_metadata(value)


def build_alert_signals(
    *,
    metrics: QualityMetrics,
    policy: QualityPolicy,
    clock: Clock,
) -> tuple[AlertSignal, ...]:
    now = clock.now()
    signals: list[AlertSignal] = []
    if metrics.critical_quality_failures_total > 0:
        signals.append(
            _signal(
                signal_type=AlertSignalType.CRITICAL_RULE_FAILURE,
                severity=QualitySeverity.CRITICAL,
                count=metrics.critical_quality_failures_total,
                now=now,
                reason_code="critical_quality_failure",
            )
        )
    total = metrics.events_evaluated_total
    thresholds = policy.sustained_failure_thresholds
    if total >= thresholds.minimum_events:
        rejection_rate = (metrics.events_rejected_total / total) * 100
        if rejection_rate >= float(thresholds.rejection_rate_percent):
            signals.append(
                _signal(
                    signal_type=AlertSignalType.SUSTAINED_REJECTION_RATE,
                    severity=QualitySeverity.ERROR,
                    count=metrics.events_rejected_total,
                    now=now,
                    reason_code="sustained_rejection_rate",
                    dimensions={"rate_percent": f"{rejection_rate:.3f}"},
                )
            )
        stale = metrics.rule_failures.get("freshness.event_stale", 0)
        stale_rate = (stale / total) * 100
        if stale_rate >= float(thresholds.stale_rate_percent):
            signals.append(
                _signal(
                    signal_type=AlertSignalType.SUSTAINED_STALE_RATE,
                    severity=QualitySeverity.WARNING,
                    count=stale,
                    now=now,
                    reason_code="sustained_stale_rate",
                    dimensions={"rate_percent": f"{stale_rate:.3f}"},
                )
            )
    if metrics.freshness_failures_total > 0:
        signals.append(
            _signal(
                signal_type=AlertSignalType.FRESHNESS_BREACH,
                severity=QualitySeverity.WARNING,
                count=metrics.freshness_failures_total,
                now=now,
                reason_code="freshness_breach",
            )
        )
    if metrics.operational_failures_total > 0:
        signals.append(
            _signal(
                signal_type=AlertSignalType.REPEATED_OPERATIONAL_FAILURE,
                severity=QualitySeverity.ERROR,
                count=metrics.operational_failures_total,
                now=now,
                reason_code="repeated_operational_failure",
            )
        )
    if metrics.operational_outcomes.get("publish_failed", 0) > 0:
        signals.append(
            _signal(
                signal_type=AlertSignalType.REPEATED_PUBLISH_FAILURE,
                severity=QualitySeverity.ERROR,
                count=metrics.operational_outcomes["publish_failed"],
                now=now,
                reason_code="operational_publish_failed",
            )
        )
    if metrics.operational_outcomes.get("writer_failed", 0) > 0:
        signals.append(
            _signal(
                signal_type=AlertSignalType.WRITER_FAILURE,
                severity=QualitySeverity.ERROR,
                count=metrics.operational_outcomes["writer_failed"],
                now=now,
                reason_code="operational_writer_failed",
            )
        )
    if metrics.operational_outcomes.get("checkpoint_failed", 0) > 0:
        signals.append(
            _signal(
                signal_type=AlertSignalType.CHECKPOINT_FAILURE,
                severity=QualitySeverity.ERROR,
                count=metrics.operational_outcomes["checkpoint_failed"],
                now=now,
                reason_code="operational_checkpoint_failed",
            )
        )
    if metrics.operational_outcomes.get("replay_failed", 0) > 0:
        signals.append(
            _signal(
                signal_type=AlertSignalType.REPLAY_FAILURE,
                severity=QualitySeverity.ERROR,
                count=metrics.operational_outcomes["replay_failed"],
                now=now,
                reason_code="operational_replay_failed",
            )
        )
    if metrics.operational_outcomes.get("backfill_failed", 0) > 0:
        signals.append(
            _signal(
                signal_type=AlertSignalType.BACKFILL_FAILURE,
                severity=QualitySeverity.ERROR,
                count=metrics.operational_outcomes["backfill_failed"],
                now=now,
                reason_code="operational_backfill_failed",
            )
        )
    if metrics.operational_outcomes.get("admission_overflow", 0) > 0:
        signals.append(
            _signal(
                signal_type=AlertSignalType.ADMISSION_OVERFLOW,
                severity=QualitySeverity.ERROR,
                count=metrics.operational_outcomes["admission_overflow"],
                now=now,
                reason_code="operational_admission_overflow",
            )
        )
    return tuple(sorted(signals, key=lambda signal: signal.signal_id))


def _signal(
    *,
    signal_type: AlertSignalType,
    severity: QualitySeverity,
    count: int,
    now: datetime,
    reason_code: str,
    dimensions: dict[str, str] | None = None,
) -> AlertSignal:
    return AlertSignal(
        signal_id=f"quality.{signal_type.value}",
        signal_type=signal_type,
        severity=severity,
        first_seen_at=now,
        last_seen_at=now,
        count=count,
        dimensions=dimensions or {},
        reason_code=reason_code,
    )
