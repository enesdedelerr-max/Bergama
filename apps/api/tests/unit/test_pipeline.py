"""Unit tests for MarketDataOrchestrator pipeline (#305)."""

from __future__ import annotations

import asyncio
from datetime import timedelta

import pytest
from app.core.clock import FixedClock
from app.core.orchestrator_settings import OrchestratorSettings
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.orchestrator.context import PipelineContext
from app.market_data.orchestrator.errors import OrchestratorConfigurationError
from app.market_data.orchestrator.pipeline import (
    MarketDataOrchestrator,
    build_market_data_orchestrator,
)
from app.market_data.orchestrator.policies import TERMINAL_DECISIONS, PipelineDecision
from app.market_data.orchestrator.ports import DryRunPublishPort, PublishResult
from app.market_data.orchestrator.stages import initial_context
from app.market_data.quality import DataQualityFlags
from tests.support.orchestrator_events import (
    EVENT_TIME,
    pit_invalid_trade,
    revision_trade,
    trade_event,
)
from tests.support.provider_contracts.clocks import OBSERVED_AT
from tests.support.recording_publish_port import RecordingPublishPort


def _settings(**overrides: object) -> OrchestratorSettings:
    base: dict[str, object] = {
        "enabled": True,
        "pipeline_name": "test-pipeline",
        "max_in_flight": 8,
        "admission_timeout_seconds": 0.2,
        "dedup_ttl_seconds": 3600.0,
        "dedup_max_entries": 1000,
    }
    base.update(overrides)
    return OrchestratorSettings(**base)  # type: ignore[arg-type]


def _orchestrator(**overrides: object) -> tuple[MarketDataOrchestrator, RecordingPublishPort]:
    clock = FixedClock(OBSERVED_AT)
    port = RecordingPublishPort(clock=clock)
    orch = build_market_data_orchestrator(
        _settings(**overrides),
        clock=clock,
        publish_port=port,
    )
    return orch, port


class GatedPublishPort:
    """Blocks inside publish until release is set — for concurrent pressure tests."""

    def __init__(self, *, clock: FixedClock) -> None:
        self._clock = clock
        self.entered = asyncio.Event()
        self.release = asyncio.Event()
        self.calls = 0

    async def publish(
        self,
        event: CanonicalMarketEvent,
        *,
        routing_key: str,
        context: PipelineContext,
    ) -> PublishResult:
        _ = routing_key, context
        self.calls += 1
        self.entered.set()
        await self.release.wait()
        return PublishResult(ok=True, published_at=self._clock.now(), detail="gated")


def test_build_requires_publish_port_when_not_dry_run() -> None:
    with pytest.raises(OrchestratorConfigurationError, match="publish_port_required"):
        build_market_data_orchestrator(
            _settings(enabled=True, dry_run=False),
            clock=FixedClock(OBSERVED_AT),
            publish_port=None,
        )


def test_build_rejects_disabled_settings() -> None:
    with pytest.raises(OrchestratorConfigurationError, match="orchestrator.disabled"):
        build_market_data_orchestrator(
            OrchestratorSettings(enabled=False),
            clock=FixedClock(OBSERVED_AT),
            publish_port=RecordingPublishPort(),
        )


@pytest.mark.asyncio
async def test_pipeline_publishes_successfully() -> None:
    orch, port = _orchestrator()
    result = await orch.process(trade_event(), correlation_id="c-1")
    assert result.decision is PipelineDecision.PUBLISHED
    assert result.decision in TERMINAL_DECISIONS
    assert result.routing_key == "market.trade"
    assert result.audit[-1].decision is PipelineDecision.PUBLISHED
    assert any(r.decision is PipelineDecision.ACCEPTED for r in result.audit)
    assert len(port.published) == 1
    assert orch.metrics.published == 1
    assert orch.metrics.accepted == 1


@pytest.mark.asyncio
async def test_pipeline_suppresses_duplicate_with_audit() -> None:
    orch, port = _orchestrator()
    first = await orch.process(trade_event(source_event_id="dup-1"))
    second = await orch.process(trade_event(source_event_id="dup-1"))
    assert first.decision is PipelineDecision.PUBLISHED
    assert second.decision is PipelineDecision.DUPLICATE_SUPPRESSED
    assert len(port.published) == 1
    assert orch.metrics.duplicate_suppressed == 1
    assert second.audit[-1].decision is PipelineDecision.DUPLICATE_SUPPRESSED


@pytest.mark.asyncio
async def test_publish_failure_releases_reservation_and_allows_replay() -> None:
    orch, port = _orchestrator()
    port.set_fail_next(True)
    failed = await orch.process(trade_event(source_event_id="retry-1"))
    assert failed.decision is PipelineDecision.PUBLISH_FAILED
    assert failed.decision is not PipelineDecision.ACCEPTED
    assert len(port.published) == 0
    replay = await orch.process(trade_event(source_event_id="retry-1"))
    assert replay.decision is PipelineDecision.PUBLISHED
    assert len(port.published) == 1


@pytest.mark.asyncio
async def test_revision_never_treated_as_duplicate() -> None:
    orch, port = _orchestrator()
    original = await orch.process(trade_event(source_event_id="same-sid"))
    revision = await orch.process(revision_trade(of_source_id="same-sid"))
    assert original.decision is PipelineDecision.PUBLISHED
    assert revision.decision is PipelineDecision.PUBLISHED
    assert len(port.published) == 2


@pytest.mark.asyncio
async def test_pipeline_rejects_pit_violation() -> None:
    orch, port = _orchestrator()
    result = await orch.process(pit_invalid_trade())
    assert result.decision is PipelineDecision.REJECTED_PIT
    assert len(port.published) == 0
    assert orch.metrics.rejected_pit == 1


@pytest.mark.asyncio
async def test_pipeline_batch_preserves_order_no_global_sort() -> None:
    orch, port = _orchestrator()
    early = trade_event(source_event_id="early", occurred_at=EVENT_TIME)
    late = trade_event(
        source_event_id="late",
        occurred_at=EVENT_TIME + timedelta(minutes=5),
    )
    results = await orch.process_batch([late, early])
    assert [r.event.source.source_event_id for r in results] == ["late", "early"]
    assert [e.source.source_event_id for e, _, _ in port.published] == ["late", "early"]


@pytest.mark.asyncio
async def test_admission_timeout_under_real_concurrent_pressure() -> None:
    clock = FixedClock(OBSERVED_AT)
    gated = GatedPublishPort(clock=clock)
    orch = build_market_data_orchestrator(
        _settings(max_in_flight=1, admission_timeout_seconds=0.05),
        clock=clock,
        publish_port=gated,
    )

    async def first() -> PipelineContext:
        return await orch.process(trade_event(source_event_id="hold-1"))

    task = asyncio.create_task(first())
    await gated.entered.wait()

    overflow = await orch.process(trade_event(source_event_id="overflow-1"))
    assert overflow.decision is PipelineDecision.BUFFER_OVERFLOW
    assert overflow.audit[-1].decision is PipelineDecision.BUFFER_OVERFLOW
    assert orch.metrics.buffer_overflow == 1
    assert gated.calls == 1

    gated.release.set()
    held = await task
    assert held.decision is PipelineDecision.PUBLISHED

    # Capacity released — unrelated event proceeds.
    later = await orch.process(trade_event(source_event_id="after-1"))
    assert later.decision is PipelineDecision.PUBLISHED
    assert gated.calls == 2


@pytest.mark.asyncio
async def test_concurrent_same_key_publishes_at_most_once() -> None:
    clock = FixedClock(OBSERVED_AT)
    gated = GatedPublishPort(clock=clock)
    orch = build_market_data_orchestrator(
        _settings(max_in_flight=4, admission_timeout_seconds=1.0),
        clock=clock,
        publish_port=gated,
    )

    async def run() -> PipelineContext:
        return await orch.process(trade_event(source_event_id="race-1"))

    t1 = asyncio.create_task(run())
    await gated.entered.wait()
    t2 = asyncio.create_task(run())
    second = await t2
    assert second.decision is PipelineDecision.DUPLICATE_SUPPRESSED
    gated.release.set()
    first = await t1
    assert first.decision is PipelineDecision.PUBLISHED
    assert gated.calls == 1


@pytest.mark.asyncio
async def test_publish_failed_decision_not_accepted() -> None:
    orch, port = _orchestrator()
    port.set_fail_next(True)
    result = await orch.process(trade_event(source_event_id="pub-fail"))
    assert result.decision is PipelineDecision.PUBLISH_FAILED
    assert result.audit[-1].decision is PipelineDecision.PUBLISH_FAILED
    assert len(port.published) == 0


@pytest.mark.asyncio
async def test_dry_run_is_observable_not_published() -> None:
    clock = FixedClock(OBSERVED_AT)
    orch = build_market_data_orchestrator(
        _settings(dry_run=True),
        clock=clock,
        publish_port=None,
    )
    assert isinstance(orch.publish_port, DryRunPublishPort)
    result = await orch.process(trade_event(source_event_id="dry-1"))
    assert result.decision is PipelineDecision.DRY_RUN
    assert orch.metrics.published == 0
    assert orch.metrics.dry_run == 1
    # Reservation released — replay after dry-run is allowed.
    again = await orch.process(trade_event(source_event_id="dry-1"))
    assert again.decision is PipelineDecision.DRY_RUN


@pytest.mark.asyncio
async def test_quality_flags_preserved() -> None:
    orch, _port = _orchestrator()
    event = trade_event(
        source_event_id="late-1",
        quality=DataQualityFlags(is_late=True, late_arrival_lag_ms=5),
    )
    result = await orch.process(event)
    assert result.decision is PipelineDecision.PUBLISHED
    assert result.quality.is_late is True
    assert result.quality.late_arrival_lag_ms == 5


@pytest.mark.asyncio
async def test_aclose_idempotent() -> None:
    orch, _port = _orchestrator()
    await orch.aclose()
    await orch.aclose()
    with pytest.raises(RuntimeError, match="closed"):
        await orch.process(trade_event())


def test_context_type() -> None:
    clock = FixedClock(OBSERVED_AT)
    ctx = initial_context(trade_event(), clock=clock, correlation_id="x")
    assert isinstance(ctx, PipelineContext)
