"""Data-quality metrics, snapshots, alerts and quarantine tests (#310)."""

from __future__ import annotations

from app.core.clock import FixedClock
from app.market_data.data_quality import (
    DataQualityService,
    InMemoryQuarantinePort,
    QualityMetrics,
    QualityOperationalOutcomeType,
    QualityRuleId,
    QualitySeverity,
    build_alert_signals,
    build_quality_snapshot,
    default_quality_policy,
)
from tests.support.orchestrator_events import EVENT_TIME, trade_event


def test_metrics_snapshot_is_bounded_and_payload_free() -> None:
    policy = default_quality_policy()
    metrics = QualityMetrics(max_tracked_instruments=1, max_problem_dimensions=3)
    service = DataQualityService(policy=policy, clock=FixedClock(EVENT_TIME), metrics=metrics)
    service.evaluate(trade_event())
    service.record_operational_outcome(
        QualityOperationalOutcomeType.REPLAY_FAILED,
        reason_code="replay_checkpoint_failed",
    )

    snapshot = build_quality_snapshot(metrics=metrics, policy=policy, clock=FixedClock(EVENT_TIME))
    counts = metrics.snapshot_counts()
    assert snapshot.policy_fingerprint == policy.fingerprint()
    assert snapshot.evaluated_count == 1
    assert snapshot.counts_by_action["accept"] == 1
    assert snapshot.lag_statistics["event_age_seconds"].count == 0
    assert snapshot.top_problem_dimensions["operational_outcome"]["replay_failed"] == 1
    assert counts["operational_failures_total"] == 1
    assert "payload" not in snapshot.model_dump_json()
    assert snapshot.known_limitations
    assert snapshot.pipeline_health_summary["quality_events_evaluated"] == "1"


def test_alert_signals_are_generated_without_external_send() -> None:
    policy = default_quality_policy()
    metrics = QualityMetrics()
    metrics.critical_quality_failures_total = 1
    metrics.events_evaluated_total = 10
    metrics.events_rejected_total = 5
    metrics.rule_failures[QualityRuleId.FRESHNESS_EVENT_STALE.value] = 5
    metrics.freshness_failures_total = 5
    for outcome_type in QualityOperationalOutcomeType:
        metrics.record_operational_outcome(outcome_type)

    signals = build_alert_signals(metrics=metrics, policy=policy, clock=FixedClock(EVENT_TIME))
    signal_types = {signal.signal_type.value for signal in signals}
    assert "critical_rule_failure" in signal_types
    assert "sustained_rejection_rate" in signal_types
    assert "sustained_stale_rate" in signal_types
    assert "freshness_breach" in signal_types
    assert "repeated_operational_failure" in signal_types
    assert "repeated_publish_failure" in signal_types
    assert "writer_failure" in signal_types
    assert "checkpoint_failure" in signal_types
    assert "replay_failure" in signal_types
    assert "backfill_failure" in signal_types
    assert "admission_overflow" in signal_types
    assert all("payload" not in signal.model_dump_json() for signal in signals)


async def test_in_memory_quarantine_stores_safe_summary_only() -> None:
    policy = default_quality_policy(
        observe_only=False,
        reject_on_error=True,
        quarantine_on_error=True,
    ).model_copy(
        update={
            "severity_overrides": {
                QualityRuleId.FRESHNESS_EVENT_STALE: QualitySeverity.ERROR,
            }
        }
    )
    port = InMemoryQuarantinePort()
    service = DataQualityService(policy=policy, clock=FixedClock(EVENT_TIME), quarantine_port=port)
    assessment = service.evaluate(trade_event())
    result = await service.quarantine(
        trade_event(),
        assessment=assessment,
        correlation_id="corr-1",
    )
    assert result.succeeded is True
    assert len(port.records) == 1
    assert port.records[0].assessment_id == assessment.assessment_id
    assert "payload" not in repr(port.records[0]).lower()
