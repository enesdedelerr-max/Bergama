"""Unit tests for PublishPort implementations (#305)."""

from __future__ import annotations

import pytest
from app.core.clock import FixedClock
from app.market_data.orchestrator.context import PipelineContext
from app.market_data.orchestrator.policies import PipelineDecision
from app.market_data.orchestrator.ports import DryRunPublishPort, PublishResult
from tests.support.orchestrator_events import trade_event
from tests.support.provider_contracts.clocks import OBSERVED_AT
from tests.support.recording_publish_port import RecordingPublishPort


def _context() -> PipelineContext:
    clock = FixedClock(OBSERVED_AT)
    event = trade_event()
    return PipelineContext(
        event=event,
        dedup_key="k",
        idempotency_key="i",
        routing_key="market.trade",
        decision=PipelineDecision.PENDING,
        quality=event.quality,
        received_at=clock.now(),
        pipeline_clock=clock,
        correlation_id=None,
        audit=(),
    )


@pytest.mark.asyncio
async def test_dry_run_publish_port_never_succeeds() -> None:
    clock = FixedClock(OBSERVED_AT)
    port = DryRunPublishPort(clock=clock)
    ctx = _context()
    result = await port.publish(ctx.event, routing_key="market.trade", context=ctx)
    assert result.succeeded is False
    assert result.safe_metadata.get("dry_run") == "true"
    assert not hasattr(result, "topic")
    assert not hasattr(result, "partition")
    assert not hasattr(result, "offset")


@pytest.mark.asyncio
async def test_recording_publish_port_records_and_can_fail() -> None:
    clock = FixedClock(OBSERVED_AT)
    port = RecordingPublishPort(clock=clock)
    ctx = _context()
    ok = await port.publish(ctx.event, routing_key="market.trade", context=ctx)
    assert ok.succeeded is True
    assert ok.sink_message_id is not None
    assert ok.idempotency_acknowledged is True
    assert len(port.published) == 1
    port.set_fail_next(True)
    failed = await port.publish(ctx.event, routing_key="market.trade", context=ctx)
    assert failed.succeeded is False
    assert len(port.published) == 1


def test_publish_result_rejects_secret_metadata_keys() -> None:
    with pytest.raises(ValueError, match="forbidden"):
        PublishResult(
            succeeded=True,
            published_at=OBSERVED_AT,
            safe_metadata={"api_key": "nope"},
        )
