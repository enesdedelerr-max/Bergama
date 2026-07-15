"""Deterministic quality monitoring snapshots (#310)."""

from __future__ import annotations

from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.clock import Clock
from app.market_data.data_quality.metrics import QualityMetrics
from app.market_data.data_quality.policy import QualityPolicy
from app.market_data.timing import require_utc_aware


class LagStatistics(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    count: int = Field(ge=0)
    min_seconds: int | None = Field(default=None, ge=0)
    max_seconds: int | None = Field(default=None, ge=0)
    avg_seconds: float | None = Field(default=None, ge=0)


class QualitySnapshot(BaseModel):
    """Payload-free bounded quality monitoring snapshot."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    window_start: datetime
    window_end: datetime
    generated_at: datetime
    policy_fingerprint: str = Field(min_length=64, max_length=64)
    evaluated_count: int = Field(ge=0)
    counts_by_status: dict[str, int]
    counts_by_severity: dict[str, int]
    counts_by_action: dict[str, int]
    counts_by_rule: dict[str, int]
    lag_statistics: dict[str, LagStatistics]
    top_problem_dimensions: dict[str, dict[str, int]]
    critical_halt_active: bool = False
    pipeline_health_summary: dict[str, str]
    known_limitations: tuple[str, ...]

    @field_validator("window_start", "window_end", "generated_at")
    @classmethod
    def utc_times(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="snapshot_time")


def build_quality_snapshot(
    *,
    metrics: QualityMetrics,
    policy: QualityPolicy,
    clock: Clock,
    critical_halt_active: bool = False,
) -> QualitySnapshot:
    generated_at = clock.now()
    window_start = generated_at - timedelta(seconds=policy.aggregation_window_seconds)
    return QualitySnapshot(
        window_start=window_start,
        window_end=generated_at,
        generated_at=generated_at,
        policy_fingerprint=policy.fingerprint(),
        evaluated_count=metrics.events_evaluated_total,
        counts_by_status=dict(sorted(metrics.status_counts.items())),
        counts_by_severity=dict(sorted(metrics.severity_counts.items())),
        counts_by_action=dict(sorted(metrics.action_counts.items())),
        counts_by_rule=dict(
            sorted(
                metrics.rule_failures.items(),
                key=lambda item: (-item[1], item[0]),
            )[: metrics.max_problem_dimensions]
        ),
        lag_statistics={
            "event_age_seconds": _lag_stats(metrics.event_age_seconds),
            "ingestion_lag_seconds": _lag_stats(metrics.ingestion_lag_seconds),
            "known_to_ingested_lag_seconds": _lag_stats(metrics.known_to_ingested_lag_seconds),
        },
        top_problem_dimensions={
            "source_provider": dict(
                sorted(
                    metrics.source_provider_counts.items(),
                    key=lambda item: (-item[1], item[0]),
                )[: metrics.max_problem_dimensions]
            ),
            "instrument_key": dict(
                sorted(
                    metrics.tracked_instrument_counts.items(),
                    key=lambda item: (-item[1], item[0]),
                )[: metrics.max_problem_dimensions]
            ),
            "event_type": dict(sorted(metrics.event_type_counts.items())),
            "operational_outcome": dict(
                sorted(
                    metrics.operational_outcomes.items(),
                    key=lambda item: (-item[1], item[0]),
                )[: metrics.max_problem_dimensions]
            ),
        },
        critical_halt_active=critical_halt_active,
        pipeline_health_summary={
            "quality_events_evaluated": str(metrics.events_evaluated_total),
            "critical_quality_failures": str(metrics.critical_quality_failures_total),
        },
        known_limitations=(
            "process-local only; counters reset on container close",
            "no Prometheus exporter in #310",
            "no generic continuity gap rule without cadence policy",
        ),
    )


def _lag_stats(values: list[int]) -> LagStatistics:
    if not values:
        return LagStatistics(count=0)
    total = sum(values)
    return LagStatistics(
        count=len(values),
        min_seconds=min(values),
        max_seconds=max(values),
        avg_seconds=round(total / len(values), 3),
    )
