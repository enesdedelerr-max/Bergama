"""Bounded process-local data-quality metrics (#310)."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from app.market_data.data_quality.models import (
    QualityAssessment,
    QualityOperationalOutcomeType,
    QualityRuleId,
)


@dataclass(slots=True)
class QualityMetrics:
    """In-process bounded counters owned by one container."""

    max_tracked_instruments: int = 128
    max_problem_dimensions: int = 20
    events_evaluated_total: int = 0
    events_accepted_total: int = 0
    events_degraded_total: int = 0
    events_rejected_total: int = 0
    events_quarantined_total: int = 0
    critical_quality_failures_total: int = 0
    quarantine_failed_total: int = 0
    freshness_failures_total: int = 0
    pit_failures_total: int = 0
    value_failures_total: int = 0
    duplicate_observations_total: int = 0
    operational_failures_total: int = 0
    status_counts: Counter[str] = field(default_factory=Counter)
    severity_counts: Counter[str] = field(default_factory=Counter)
    action_counts: Counter[str] = field(default_factory=Counter)
    rule_failures: Counter[str] = field(default_factory=Counter)
    operational_outcomes: Counter[str] = field(default_factory=Counter)
    event_type_counts: Counter[str] = field(default_factory=Counter)
    source_provider_counts: Counter[str] = field(default_factory=Counter)
    tracked_instrument_counts: Counter[str] = field(default_factory=Counter)
    ingestion_lag_seconds: list[int] = field(default_factory=list)
    known_to_ingested_lag_seconds: list[int] = field(default_factory=list)
    event_age_seconds: list[int] = field(default_factory=list)

    def record_assessment(self, assessment: QualityAssessment) -> None:
        self.events_evaluated_total += 1
        self.status_counts[assessment.overall_status.value] += 1
        self.severity_counts[assessment.highest_severity.value] += 1
        self.action_counts[assessment.recommended_action.value] += 1
        self.event_type_counts[assessment.event_type] += 1
        provider = assessment.safe_metadata.get("source_provider")
        if provider:
            self.source_provider_counts[provider] += 1
        if self.max_tracked_instruments > 0 and (
            assessment.instrument_key in self.tracked_instrument_counts
            or len(self.tracked_instrument_counts) < self.max_tracked_instruments
        ):
            self.tracked_instrument_counts[assessment.instrument_key] += 1
        for result in assessment.rule_results:
            if result.passed:
                continue
            self.rule_failures[result.rule_id.value] += 1
            if result.rule_id is QualityRuleId.FRESHNESS_INGESTION_LAG:
                self.freshness_failures_total += 1
                _append_int(self.ingestion_lag_seconds, result.measured_value)
            elif result.rule_id is QualityRuleId.FRESHNESS_KNOWN_TO_INGESTED_LAG:
                self.freshness_failures_total += 1
                _append_int(self.known_to_ingested_lag_seconds, result.measured_value)
            elif result.rule_id is QualityRuleId.FRESHNESS_EVENT_STALE:
                self.freshness_failures_total += 1
                _append_int(self.event_age_seconds, result.measured_value)
            elif result.rule_id is QualityRuleId.PIT_INVALID_ORDER:
                self.pit_failures_total += 1
            elif result.rule_id.value.startswith("value."):
                self.value_failures_total += 1
            elif result.rule_id is QualityRuleId.DUPLICATION_DUPLICATE_OBSERVATION:
                self.duplicate_observations_total += 1
            elif result.rule_id.value.startswith("operational."):
                self.operational_failures_total += 1
        match assessment.recommended_action.value:
            case "accept":
                self.events_accepted_total += 1
            case "accept_degraded":
                self.events_degraded_total += 1
            case "reject":
                self.events_rejected_total += 1
            case "quarantine":
                # Actual quarantine success/failure is recorded separately.
                pass
            case "halt_pipeline":
                self.critical_quality_failures_total += 1

    def record_quarantine(self, succeeded: bool) -> None:
        if succeeded:
            self.events_quarantined_total += 1
        else:
            self.quarantine_failed_total += 1

    def record_operational_outcome(
        self,
        outcome_type: QualityOperationalOutcomeType,
    ) -> None:
        self.operational_failures_total += 1
        self.operational_outcomes[outcome_type.value] += 1
        rule_id = _rule_id_for_operational_outcome(outcome_type)
        self.rule_failures[rule_id.value] += 1

    def snapshot_counts(self) -> dict[str, object]:
        return {
            "events_evaluated_total": self.events_evaluated_total,
            "events_accepted_total": self.events_accepted_total,
            "events_degraded_total": self.events_degraded_total,
            "events_rejected_total": self.events_rejected_total,
            "events_quarantined_total": self.events_quarantined_total,
            "critical_quality_failures_total": self.critical_quality_failures_total,
            "quarantine_failed_total": self.quarantine_failed_total,
            "freshness_failures_total": self.freshness_failures_total,
            "pit_failures_total": self.pit_failures_total,
            "value_failures_total": self.value_failures_total,
            "duplicate_observations_total": self.duplicate_observations_total,
            "operational_failures_total": self.operational_failures_total,
            "status_counts": dict(sorted(self.status_counts.items())),
            "severity_counts": dict(sorted(self.severity_counts.items())),
            "action_counts": dict(sorted(self.action_counts.items())),
            "rule_failures": _top(self.rule_failures, self.max_problem_dimensions),
            "operational_outcomes": _top(
                self.operational_outcomes,
                self.max_problem_dimensions,
            ),
            "event_type_counts": dict(sorted(self.event_type_counts.items())),
            "source_provider_counts": _top(
                self.source_provider_counts,
                self.max_problem_dimensions,
            ),
            "tracked_instrument_counts": _top(
                self.tracked_instrument_counts,
                self.max_problem_dimensions,
            ),
        }

    def clear(self) -> None:
        self.events_evaluated_total = 0
        self.events_accepted_total = 0
        self.events_degraded_total = 0
        self.events_rejected_total = 0
        self.events_quarantined_total = 0
        self.critical_quality_failures_total = 0
        self.quarantine_failed_total = 0
        self.freshness_failures_total = 0
        self.pit_failures_total = 0
        self.value_failures_total = 0
        self.duplicate_observations_total = 0
        self.operational_failures_total = 0
        self.status_counts.clear()
        self.severity_counts.clear()
        self.action_counts.clear()
        self.rule_failures.clear()
        self.operational_outcomes.clear()
        self.event_type_counts.clear()
        self.source_provider_counts.clear()
        self.tracked_instrument_counts.clear()
        self.ingestion_lag_seconds.clear()
        self.known_to_ingested_lag_seconds.clear()
        self.event_age_seconds.clear()


def _append_int(values: list[int], raw: str | None) -> None:
    if raw is None:
        return
    try:
        values.append(max(0, int(raw)))
    except ValueError:
        return


def _top(counter: Counter[str], limit: int) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit])


def _rule_id_for_operational_outcome(
    outcome_type: QualityOperationalOutcomeType,
) -> QualityRuleId:
    match outcome_type:
        case QualityOperationalOutcomeType.PUBLISH_FAILED:
            return QualityRuleId.OPERATIONAL_PUBLISH_FAILED
        case QualityOperationalOutcomeType.WRITER_FAILED:
            return QualityRuleId.OPERATIONAL_WRITER_FAILED
        case QualityOperationalOutcomeType.CHECKPOINT_FAILED:
            return QualityRuleId.OPERATIONAL_CHECKPOINT_FAILED
        case QualityOperationalOutcomeType.ADMISSION_OVERFLOW:
            return QualityRuleId.OPERATIONAL_ADMISSION_OVERFLOW
        case (
            QualityOperationalOutcomeType.REPLAY_FAILED
            | QualityOperationalOutcomeType.BACKFILL_FAILED
        ):
            return QualityRuleId.OPERATIONAL_CHECKPOINT_FAILED
