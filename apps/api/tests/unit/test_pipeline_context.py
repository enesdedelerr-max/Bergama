"""Unit tests for PipelineContext immutability (#305)."""

from __future__ import annotations

from app.core.clock import FixedClock
from app.market_data.orchestrator.context import PipelineContext
from app.market_data.orchestrator.policies import PipelineDecision
from app.market_data.quality import DataQualityFlags
from tests.support.orchestrator_events import trade_event
from tests.support.provider_contracts.clocks import OBSERVED_AT


def test_pipeline_context_is_immutable_and_evolve_returns_new() -> None:
    clock = FixedClock(OBSERVED_AT)
    event = trade_event()
    ctx = PipelineContext(
        event=event,
        dedup_key=None,
        idempotency_key=None,
        routing_key=None,
        decision=PipelineDecision.PENDING,
        quality=event.quality,
        received_at=clock.now(),
        pipeline_clock=clock,
        correlation_id="corr-1",
        audit=(),
        metadata={},
    )
    updated = ctx.evolve(
        decision=PipelineDecision.ACCEPTED,
        routing_key="market.trade",
        metadata={"k": "v"},
    )
    assert ctx.decision is PipelineDecision.PENDING
    assert ctx.routing_key is None
    assert updated.decision is PipelineDecision.ACCEPTED
    assert updated.routing_key == "market.trade"
    assert updated.metadata == {"k": "v"}
    assert updated.correlation_id == "corr-1"
    assert updated.quality == DataQualityFlags()
