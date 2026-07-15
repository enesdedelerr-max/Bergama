"""Data-quality orchestrator integration tests (#310)."""

from __future__ import annotations

import pytest
from app.core.clock import FixedClock
from app.core.orchestrator_settings import OrchestratorSettings
from app.market_data.data_quality import (
    DataQualityService,
    InMemoryQuarantinePort,
    QualityRuleId,
    QualitySeverity,
    default_quality_policy,
)
from app.market_data.orchestrator import PipelineDecision, build_market_data_orchestrator
from tests.support.orchestrator_events import trade_event
from tests.support.provider_contracts.clocks import OBSERVED_AT
from tests.support.recording_publish_port import RecordingPublishPort


def _settings() -> OrchestratorSettings:
    return OrchestratorSettings(
        enabled=True,
        pipeline_name="quality-integration",
        max_in_flight=8,
        admission_timeout_seconds=0.2,
    )


@pytest.mark.asyncio
async def test_observe_only_degraded_quality_still_publishes() -> None:
    clock = FixedClock(OBSERVED_AT)
    policy = default_quality_policy(observe_only=True)
    service = DataQualityService(policy=policy, clock=clock)
    port = RecordingPublishPort(clock=clock)
    orch = build_market_data_orchestrator(
        _settings(),
        clock=clock,
        publish_port=port,
        data_quality_service=service,
    )
    result = await orch.process(trade_event())
    assert result.decision is PipelineDecision.PUBLISHED
    assert result.context.quality_assessment is not None
    assert result.context.quality_assessment.recommended_action.value == "accept_degraded"
    assert orch.metrics.quality_degraded_total == 1
    assert len(port.published) == 1


@pytest.mark.asyncio
async def test_quality_reject_does_not_publish() -> None:
    clock = FixedClock(OBSERVED_AT)
    policy = _enforcing_stale_policy(quarantine=False)
    service = DataQualityService(policy=policy, clock=clock)
    port = RecordingPublishPort(clock=clock)
    orch = build_market_data_orchestrator(
        _settings(),
        clock=clock,
        publish_port=port,
        data_quality_service=service,
    )
    result = await orch.process(trade_event(source_event_id="reject-1"))
    assert result.decision is PipelineDecision.QUALITY_REJECTED
    assert result.context.audit[-1].quality_status == "failed"
    assert orch.metrics.quality_rejected_total == 1
    assert port.published == []


@pytest.mark.asyncio
async def test_quality_quarantine_requires_explicit_port_and_never_publishes() -> None:
    clock = FixedClock(OBSERVED_AT)
    policy = _enforcing_stale_policy(quarantine=True)
    quarantine = InMemoryQuarantinePort()
    service = DataQualityService(policy=policy, clock=clock, quarantine_port=quarantine)
    port = RecordingPublishPort(clock=clock)
    orch = build_market_data_orchestrator(
        _settings(),
        clock=clock,
        publish_port=port,
        data_quality_service=service,
    )
    result = await orch.process(trade_event(source_event_id="quarantine-1"))
    assert result.decision is PipelineDecision.QUALITY_QUARANTINED
    assert orch.metrics.quality_quarantined_total == 1
    assert len(quarantine.records) == 1
    assert port.published == []


@pytest.mark.asyncio
async def test_quarantine_without_port_fails_closed() -> None:
    clock = FixedClock(OBSERVED_AT)
    policy = _enforcing_stale_policy(quarantine=True)
    service = DataQualityService(policy=policy, clock=clock)
    port = RecordingPublishPort(clock=clock)
    orch = build_market_data_orchestrator(
        _settings(),
        clock=clock,
        publish_port=port,
        data_quality_service=service,
    )
    result = await orch.process(trade_event(source_event_id="quarantine-missing"))
    assert result.decision is PipelineDecision.QUALITY_HALT
    assert result.context.reason == "quality_quarantine_unavailable"
    assert port.published == []


@pytest.mark.asyncio
async def test_quality_critical_halt_does_not_publish() -> None:
    clock = FixedClock(OBSERVED_AT)
    policy = default_quality_policy(
        observe_only=False,
        halt_on_critical=True,
    ).model_copy(
        update={
            "severity_overrides": {
                QualityRuleId.FRESHNESS_EVENT_STALE: QualitySeverity.CRITICAL,
            }
        }
    )
    service = DataQualityService(policy=policy, clock=clock)
    port = RecordingPublishPort(clock=clock)
    orch = build_market_data_orchestrator(
        _settings(),
        clock=clock,
        publish_port=port,
        data_quality_service=service,
    )
    result = await orch.process(trade_event(source_event_id="halt-1"))
    assert result.decision is PipelineDecision.QUALITY_HALT
    assert service.critical_halt_active is True
    assert port.published == []


def _enforcing_stale_policy(*, quarantine: bool) -> object:
    return default_quality_policy(
        observe_only=False,
        reject_on_error=True,
        quarantine_on_error=quarantine,
    ).model_copy(
        update={
            "severity_overrides": {
                QualityRuleId.FRESHNESS_EVENT_STALE: QualitySeverity.ERROR,
            }
        }
    )
