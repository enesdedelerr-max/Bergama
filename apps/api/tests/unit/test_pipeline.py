"""Unit tests for MarketDataOrchestrator pipeline (#305)."""

from __future__ import annotations

import asyncio
from datetime import timedelta

import pytest
from app.core.clock import FixedClock
from app.core.orchestrator_settings import OrchestratorSettings
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.orchestrator.context import PipelineContext
from app.market_data.orchestrator.errors import (
    OrchestratorClosedError,
    OrchestratorConfigurationError,
)
from app.market_data.orchestrator.pipeline import (
    MarketDataOrchestrator,
    ProcessResult,
    build_market_data_orchestrator,
)
from app.market_data.orchestrator.policies import TERMINAL_DECISIONS, PipelineDecision
from app.market_data.orchestrator.ports import DryRunPublishPort, PublishResult
from app.market_data.orchestrator.stages import initial_context
from app.market_data.quality import DataQualityFlags
from app.market_data.timing import validate_point_in_time_order
from tests.support.orchestrator_events import (
    EVENT_TIME,
    equity,
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
        _ = routing_key, context, event
        self.calls += 1
        self.entered.set()
        await self.release.wait()
        return PublishResult(
            succeeded=True,
            published_at=self._clock.now(),
            sink_message_id="gated-1",
            idempotency_acknowledged=True,
        )


def test_build_requires_publish_port_when_not_dry_run() -> None:
    with pytest.raises(OrchestratorConfigurationError, match="publish_port_required"):
        build_market_data_orchestrator(
            _settings(enabled=True, dry_run=False),
            clock=FixedClock(OBSERVED_AT),
            publish_port=None,
        )


@pytest.mark.asyncio
async def test_pipeline_publishes_successfully() -> None:
    orch, port = _orchestrator()
    result = await orch.process(trade_event(), correlation_id="c-1")
    assert isinstance(result, ProcessResult)
    assert result.decision is PipelineDecision.PUBLISHED
    assert result.decision in TERMINAL_DECISIONS
    assert result.context.audit[-1].decision is PipelineDecision.PUBLISHED
    assert len(result.context.audit) == 1
    assert result.context.audit[-1].correlation_id == "c-1"
    assert result.context.audit[-1].event_type == "trade"
    assert not hasattr(result.context.audit[-1], "payload")
    assert "CanonicalMarketEvent" not in repr(result.context.audit[-1])
    assert len(port.published) == 1
    assert orch.metrics.published_total == 1
    assert orch.metrics.admitted_total == 1
    assert orch.metrics.in_flight_current == 0
    assert orch.metrics.publish_latency_samples == 1


@pytest.mark.asyncio
async def test_duplicate_suppressed_one_terminal_audit() -> None:
    orch, port = _orchestrator()
    first = await orch.process(trade_event(source_event_id="dup-1"))
    second = await orch.process(trade_event(source_event_id="dup-1"))
    assert first.decision is PipelineDecision.PUBLISHED
    assert second.decision is PipelineDecision.DUPLICATE_SUPPRESSED
    assert len(port.published) == 1
    assert orch.metrics.duplicate_suppressed_total == 1
    assert second.context.audit[-1].decision is second.decision
    assert len(orch.audit_sink.records()) == 2


@pytest.mark.asyncio
async def test_publish_failure_releases_reservation_and_allows_replay() -> None:
    orch, port = _orchestrator()
    port.set_fail_next(True)
    failed = await orch.process(trade_event(source_event_id="retry-1"))
    assert failed.decision is PipelineDecision.PUBLISH_FAILED
    assert failed.decision is not PipelineDecision.ACCEPTED
    assert failed.context.audit[-1].decision is PipelineDecision.PUBLISH_FAILED
    replay = await orch.process(trade_event(source_event_id="retry-1"))
    assert replay.decision is PipelineDecision.PUBLISHED


@pytest.mark.asyncio
async def test_revision_never_treated_as_duplicate() -> None:
    orch, port = _orchestrator()
    original = await orch.process(trade_event(source_event_id="same-sid"))
    revision = await orch.process(revision_trade(of_source_id="same-sid"))
    assert original.decision is PipelineDecision.PUBLISHED
    assert revision.decision is PipelineDecision.PUBLISHED
    assert len(port.published) == 2


@pytest.mark.asyncio
async def test_invalid_canonical_pit_is_rejected_validation_not_pit() -> None:
    """Invalid PIT cannot survive canonical construction — taxonomy is truthful."""
    orch, port = _orchestrator()
    result = await orch.process(pit_invalid_trade())
    assert result.decision is PipelineDecision.REJECTED_VALIDATION
    assert len(port.published) == 0
    assert orch.metrics.rejected_validation_total == 1
    assert orch.metrics.rejected_pit_total == 0


def test_pit_policy_helper_rejects_invalid_ordering_directly() -> None:
    from datetime import UTC, datetime

    from app.market_data.quality import DataQualityFlags

    ts = datetime(2024, 1, 1, tzinfo=UTC)
    later = ts + timedelta(hours=1)
    with pytest.raises(ValueError, match="occurred_at must be"):
        validate_point_in_time_order(
            occurred_at=later,
            effective_at=later,
            known_at=ts,
            ingested_at=ts,
            quality=DataQualityFlags(),
        )


@pytest.mark.asyncio
async def test_pit_stage_taxonomy_when_policy_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orch, port = _orchestrator()

    def boom(**_kwargs: object) -> None:
        raise ValueError("occurred_at must be <= known_at")

    monkeypatch.setattr(
        "app.market_data.orchestrator.stages.validate_point_in_time_order",
        boom,
    )
    result = await orch.process(trade_event(source_event_id="pit-stage"))
    assert result.decision is PipelineDecision.REJECTED_PIT
    assert orch.metrics.rejected_pit_total == 1
    assert len(port.published) == 0


@pytest.mark.asyncio
async def test_admission_timeout_under_real_concurrent_pressure() -> None:
    """Admission pressure uses a separate stream so the stream lock does not mask it."""
    clock = FixedClock(OBSERVED_AT)
    gated = GatedPublishPort(clock=clock)
    orch = build_market_data_orchestrator(
        _settings(max_in_flight=1, admission_timeout_seconds=0.05),
        clock=clock,
        publish_port=gated,
    )

    async def first() -> ProcessResult:
        return await orch.process(trade_event(source_event_id="hold-1"))

    task = asyncio.create_task(first())
    await gated.entered.wait()

    # Different instrument → different stream; can contend on in-flight admission.
    overflow = await orch.process(
        trade_event(
            source_event_id="overflow-1",
            instrument=equity(key="bergama:equity:us:msft", symbol="MSFT"),
        )
    )
    assert overflow.decision is PipelineDecision.BUFFER_OVERFLOW
    assert overflow.context.audit[-1].decision is PipelineDecision.BUFFER_OVERFLOW
    assert orch.metrics.admission_overflow_total == 1
    assert gated.calls == 1

    gated.release.set()
    held = await task
    assert held.decision is PipelineDecision.PUBLISHED
    assert orch.metrics.in_flight_current == 0

    later = await orch.process(trade_event(source_event_id="after-1"))
    assert later.decision is PipelineDecision.PUBLISHED


@pytest.mark.asyncio
async def test_concurrent_same_key_publishes_at_most_once() -> None:
    """Same-stream lock serializes work; committed dedup still suppresses the waiter."""
    clock = FixedClock(OBSERVED_AT)
    gated = GatedPublishPort(clock=clock)
    orch = build_market_data_orchestrator(
        _settings(max_in_flight=4, admission_timeout_seconds=1.0),
        clock=clock,
        publish_port=gated,
    )

    async def run() -> ProcessResult:
        return await orch.process(trade_event(source_event_id="race-1"))

    t1 = asyncio.create_task(run())
    await gated.entered.wait()
    t2 = asyncio.create_task(run())
    # t2 waits on the per-stream lock until t1 finishes publish + release.
    gated.release.set()
    first = await t1
    second = await t2
    assert first.decision is PipelineDecision.PUBLISHED
    assert second.decision is PipelineDecision.DUPLICATE_SUPPRESSED
    assert gated.calls == 1


@pytest.mark.asyncio
async def test_cancelled_waiter_does_not_deadlock_stream() -> None:
    clock = FixedClock(OBSERVED_AT)
    gated = GatedPublishPort(clock=clock)
    orch = build_market_data_orchestrator(
        _settings(max_in_flight=4, admission_timeout_seconds=1.0),
        clock=clock,
        publish_port=gated,
    )

    async def hold() -> ProcessResult:
        return await orch.process(trade_event(source_event_id="cancel-hold"))

    holder = asyncio.create_task(hold())
    await gated.entered.wait()
    waiter = asyncio.create_task(orch.process(trade_event(source_event_id="cancel-waiter")))
    await asyncio.wait({waiter}, timeout=0.05)
    waiter.cancel()
    with pytest.raises(asyncio.CancelledError):
        await waiter
    gated.release.set()
    held = await holder
    assert held.decision is PipelineDecision.PUBLISHED
    # Stream remains usable after cancelled waiter.
    follow_up = await orch.process(trade_event(source_event_id="cancel-follow"))
    assert follow_up.decision is PipelineDecision.PUBLISHED


@pytest.mark.asyncio
async def test_publish_failure_releases_stream_for_same_key_retry() -> None:
    clock = FixedClock(OBSERVED_AT)
    calls = 0

    class FailOncePort:
        async def publish(
            self,
            event: CanonicalMarketEvent,
            *,
            routing_key: str,
            context: PipelineContext,
        ) -> PublishResult:
            nonlocal calls
            _ = event, routing_key, context
            calls += 1
            if calls == 1:
                return PublishResult(succeeded=False, published_at=None)
            return PublishResult(
                succeeded=True,
                published_at=clock.now(),
                sink_message_id="ok",
                idempotency_acknowledged=True,
            )

    orch = build_market_data_orchestrator(
        _settings(),
        clock=clock,
        publish_port=FailOncePort(),
    )
    failed = await orch.process(trade_event(source_event_id="stream-fail"))
    assert failed.decision is PipelineDecision.PUBLISH_FAILED
    ok = await orch.process(trade_event(source_event_id="stream-fail"))
    assert ok.decision is PipelineDecision.PUBLISHED


@pytest.mark.asyncio
async def test_dry_run_never_published() -> None:
    clock = FixedClock(OBSERVED_AT)
    orch = build_market_data_orchestrator(
        _settings(dry_run=True),
        clock=clock,
        publish_port=None,
    )
    assert isinstance(orch.publish_port, DryRunPublishPort)
    result = await orch.process(trade_event(source_event_id="dry-1"))
    assert result.decision is PipelineDecision.DRY_RUN
    assert orch.metrics.published_total == 0
    assert orch.metrics.dry_run_total == 1


@pytest.mark.asyncio
async def test_quality_flags_preserved() -> None:
    orch, _port = _orchestrator()
    event = trade_event(
        source_event_id="late-1",
        quality=DataQualityFlags(is_late=True, late_arrival_lag_ms=5),
    )
    result = await orch.process(event)
    assert result.decision is PipelineDecision.PUBLISHED
    assert result.context.quality.is_late is True


@pytest.mark.asyncio
async def test_aclose_idempotent_and_process_fails_typed() -> None:
    orch, _port = _orchestrator()
    await orch.aclose()
    await orch.aclose()
    with pytest.raises(OrchestratorClosedError, match="orchestrator.closed"):
        await orch.process(trade_event())


@pytest.mark.asyncio
async def test_batch_preserves_submission_order() -> None:
    orch, port = _orchestrator()
    early = trade_event(source_event_id="early", occurred_at=EVENT_TIME)
    late = trade_event(
        source_event_id="late",
        occurred_at=EVENT_TIME + timedelta(minutes=5),
    )
    results = await orch.process_batch([late, early])
    assert [r.context.event.source.source_event_id for r in results] == ["late", "early"]
    assert [e.source.source_event_id for e, _, _ in port.published] == ["late", "early"]


def test_context_type() -> None:
    clock = FixedClock(OBSERVED_AT)
    ctx = initial_context(trade_event(), clock=clock, correlation_id="x")
    assert isinstance(ctx, PipelineContext)
