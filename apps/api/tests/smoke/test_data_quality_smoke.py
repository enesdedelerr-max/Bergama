"""Local synthetic data-quality smoke test (#310)."""

from __future__ import annotations

from datetime import timedelta

from app.core.clock import FixedClock
from app.market_data.data_quality import (
    DataQualityService,
    QualityMetrics,
    QualityRuleId,
    QualitySeverity,
    build_alert_signals,
    build_quality_snapshot,
    default_quality_policy,
)
from app.market_data.enums import MarketEventType
from tests.support.orchestrator_events import EVENT_TIME, trade_event


def test_data_quality_smoke_synthetic_event_snapshot_and_alerts() -> None:
    policy = default_quality_policy()
    metrics = QualityMetrics()
    service = DataQualityService(policy=policy, clock=FixedClock(EVENT_TIME), metrics=metrics)

    accepted = service.evaluate(trade_event())

    degraded_policy = default_quality_policy()
    degraded_service = DataQualityService(
        policy=degraded_policy,
        clock=FixedClock(EVENT_TIME + timedelta(minutes=10)),
        metrics=metrics,
    )
    degraded = degraded_service.evaluate(trade_event(source_event_id="t-degraded"))

    rejecting_policy = default_quality_policy(observe_only=False, reject_on_error=True).model_copy(
        update={
            "severity_overrides": {
                QualityRuleId.FRESHNESS_EVENT_STALE: QualitySeverity.ERROR,
            },
            "freshness_thresholds_by_event_type": {MarketEventType.TRADE: 1},
        }
    )
    rejecting_service = DataQualityService(
        policy=rejecting_policy,
        clock=FixedClock(EVENT_TIME + timedelta(minutes=10)),
        metrics=metrics,
    )
    rejected = rejecting_service.evaluate(trade_event(source_event_id="t-rejected"))

    snapshot = build_quality_snapshot(metrics=metrics, policy=policy, clock=FixedClock(EVENT_TIME))
    alerts = build_alert_signals(metrics=metrics, policy=policy, clock=FixedClock(EVENT_TIME))

    assert accepted.recommended_action.value == "accept"
    assert degraded.recommended_action.value == "accept_degraded"
    assert rejected.recommended_action.value == "reject"
    assert metrics.events_evaluated_total == 3
    assert metrics.events_rejected_total == 1
    assert metrics.freshness_failures_total >= 2
    assert snapshot.policy_fingerprint == policy.fingerprint()
    assert snapshot.evaluated_count == 3
    assert "freshness_breach" in {signal.signal_type.value for signal in alerts}
    assert "payload" not in snapshot.model_dump_json()
