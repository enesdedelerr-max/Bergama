"""Contract tests for Market Data Orchestrator (#305)."""

from __future__ import annotations

import asyncio
import inspect

import pytest
from app.core.clock import FixedClock
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.core.orchestrator_settings import OrchestratorSettings
from app.core.secrets import SecretSettings
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.orchestrator import (
    MarketDataOrchestrator,
    OrchestratorConfigurationError,
    PipelineDecision,
    PublishPort,
    PublishResult,
    build_market_data_orchestrator,
)
from app.market_data.orchestrator.context import PipelineContext
from app.market_data.orchestrator.policies import TERMINAL_DECISIONS
from tests.conftest import VALID_PROD_JWT_SECRET
from tests.support.orchestrator_events import bar_event, equity, quote_event, trade_event
from tests.support.provider_contracts.clocks import OBSERVED_AT
from tests.support.recording_publish_port import RecordingPublishPort


def test_publish_port_and_result_are_infrastructure_neutral() -> None:
    sig = inspect.signature(PublishPort.publish)
    params = set(sig.parameters)
    assert params == {"self", "event", "routing_key", "context"}
    fields = set(PublishResult.__dataclass_fields__)
    assert fields == {
        "succeeded",
        "published_at",
        "sink_message_id",
        "idempotency_acknowledged",
        "safe_metadata",
    }
    assert "topic" not in fields
    assert "partition" not in fields
    assert "offset" not in fields


def test_container_disabled_by_default_has_no_orchestrator() -> None:
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
    )
    assert settings.orchestrator.enabled is False
    container = build_container(settings, clock=FixedClock(OBSERVED_AT))
    assert container.market_data_orchestrator is None
    summary = settings.safe_summary()["orchestrator"]
    assert summary["enabled"] is False
    assert set(summary) == {
        "enabled",
        "dry_run",
        "pipeline_name",
        "max_in_flight",
        "admission_timeout_seconds",
        "dedup_ttl_seconds",
        "dedup_max_entries",
    }


def test_container_enabled_without_publish_port_fails_closed() -> None:
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        orchestrator=OrchestratorSettings(enabled=True, dry_run=False),
    )
    with pytest.raises(OrchestratorConfigurationError, match="publish_port_required"):
        build_container(settings, clock=FixedClock(OBSERVED_AT))


@pytest.mark.asyncio
async def test_orchestrator_end_to_end_contract() -> None:
    clock = FixedClock(OBSERVED_AT)
    port = RecordingPublishPort(clock=clock)
    orch = build_market_data_orchestrator(
        OrchestratorSettings(
            enabled=True,
            pipeline_name="contract-pipeline",
            max_in_flight=16,
        ),
        clock=clock,
        publish_port=port,
    )
    events = [
        trade_event(source_event_id="c-t1"),
        quote_event(source_event_id="c-q1"),
        bar_event(source_event_id="c-b1"),
        trade_event(source_event_id="c-t1"),
    ]
    results = await orch.process_batch(events, correlation_id="contract-1")
    decisions = [r.decision for r in results]
    assert decisions == [
        PipelineDecision.PUBLISHED,
        PipelineDecision.PUBLISHED,
        PipelineDecision.PUBLISHED,
        PipelineDecision.DUPLICATE_SUPPRESSED,
    ]
    assert all(d in TERMINAL_DECISIONS for d in decisions)
    for result in results:
        assert len(result.context.audit) == 1
        assert result.context.audit[-1].decision is result.decision
        assert result.context.audit[-1].correlation_id == "contract-1"


@pytest.mark.asyncio
async def test_container_owns_orchestrator_lifecycle_when_enabled() -> None:
    clock = FixedClock(OBSERVED_AT)
    port = RecordingPublishPort(clock=clock)
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        orchestrator=OrchestratorSettings(enabled=True, dry_run=False),
    )
    container = build_container(settings, clock=clock, publish_port=port)
    assert isinstance(container.market_data_orchestrator, MarketDataOrchestrator)
    result = await container.market_data_orchestrator.process(
        trade_event(source_event_id="container-1")
    )
    assert result.decision is PipelineDecision.PUBLISHED
    await container.aclose()
    assert container.market_data_orchestrator.closed is True


@pytest.mark.asyncio
async def test_container_dry_run_mode_is_explicit_and_not_published() -> None:
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        orchestrator=OrchestratorSettings(enabled=True, dry_run=True),
    )
    container = build_container(settings, clock=FixedClock(OBSERVED_AT))
    assert container.market_data_orchestrator is not None
    result = await container.market_data_orchestrator.process(
        trade_event(source_event_id="dry-container-1")
    )
    assert result.decision is PipelineDecision.DRY_RUN
    assert container.market_data_orchestrator.metrics.published_total == 0


@pytest.mark.asyncio
async def test_separate_containers_are_isolated() -> None:
    clock = FixedClock(OBSERVED_AT)
    shared_port = RecordingPublishPort(clock=clock)
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        orchestrator=OrchestratorSettings(enabled=True, dry_run=False),
    )
    c1 = build_container(settings, clock=clock, publish_port=shared_port)
    c2 = build_container(settings, clock=FixedClock(OBSERVED_AT), publish_port=shared_port)
    assert c1.market_data_orchestrator is not None
    assert c2.market_data_orchestrator is not None
    assert c1.market_data_orchestrator is not c2.market_data_orchestrator

    first = await c1.market_data_orchestrator.process(trade_event(source_event_id="iso-1"))
    assert first.decision is PipelineDecision.PUBLISHED
    # Same key on another container is not suppressed by c1's dedup store.
    second = await c2.market_data_orchestrator.process(trade_event(source_event_id="iso-1"))
    assert second.decision is PipelineDecision.PUBLISHED
    assert len(shared_port.published) == 2
    assert c1.market_data_orchestrator.metrics.published_total == 1
    assert c2.market_data_orchestrator.metrics.published_total == 1
    assert len(c1.market_data_orchestrator.audit_sink.records()) == 1
    assert len(c2.market_data_orchestrator.audit_sink.records()) == 1


@pytest.mark.asyncio
async def test_no_startup_publish_calls() -> None:
    clock = FixedClock(OBSERVED_AT)
    port = RecordingPublishPort(clock=clock)
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        orchestrator=OrchestratorSettings(enabled=True),
    )
    build_container(settings, clock=clock, publish_port=port)
    assert port.published == []


@pytest.mark.asyncio
async def test_admission_pressure_is_isolated_between_containers() -> None:
    clock = FixedClock(OBSERVED_AT)

    class GatedPort:
        def __init__(self) -> None:
            self.entered = asyncio.Event()
            self.release = asyncio.Event()

        async def publish(
            self,
            event: CanonicalMarketEvent,
            *,
            routing_key: str,
            context: PipelineContext,
        ) -> PublishResult:
            _ = event, routing_key, context
            self.entered.set()
            await self.release.wait()
            return PublishResult(
                succeeded=True,
                published_at=clock.now(),
                sink_message_id="gated",
                idempotency_acknowledged=True,
            )

    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        orchestrator=OrchestratorSettings(
            enabled=True,
            max_in_flight=1,
            admission_timeout_seconds=0.05,
        ),
    )
    gated = GatedPort()
    free_port = RecordingPublishPort(clock=clock)
    c1 = build_container(settings, clock=clock, publish_port=gated)
    c2 = build_container(settings, clock=FixedClock(OBSERVED_AT), publish_port=free_port)
    assert c1.market_data_orchestrator is not None
    assert c2.market_data_orchestrator is not None

    holder = asyncio.create_task(
        c1.market_data_orchestrator.process(trade_event(source_event_id="c1-hold"))
    )
    await gated.entered.wait()
    # c1 is saturated; c2 must still admit independently.
    ok = await c2.market_data_orchestrator.process(
        trade_event(
            source_event_id="c2-free",
            instrument=equity(key="bergama:equity:us:msft", symbol="MSFT"),
        )
    )
    assert ok.decision is PipelineDecision.PUBLISHED
    gated.release.set()
    held = await holder
    assert held.decision is PipelineDecision.PUBLISHED
