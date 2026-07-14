"""Contract tests for Market Data Orchestrator (#305)."""

from __future__ import annotations

import inspect

import pytest
from app.core.clock import FixedClock
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.core.orchestrator_settings import OrchestratorSettings
from app.core.secrets import SecretSettings
from app.market_data.orchestrator import (
    MarketDataOrchestrator,
    OrchestratorConfigurationError,
    PipelineDecision,
    PublishPort,
    build_market_data_orchestrator,
)
from app.market_data.orchestrator.policies import TERMINAL_DECISIONS
from tests.conftest import VALID_PROD_JWT_SECRET
from tests.support.orchestrator_events import bar_event, quote_event, trade_event
from tests.support.provider_contracts.clocks import OBSERVED_AT
from tests.support.recording_publish_port import RecordingPublishPort


def test_publish_port_has_no_kafka_or_envelope_parameters() -> None:
    sig = inspect.signature(PublishPort.publish)
    params = set(sig.parameters)
    assert "event" in params
    assert "routing_key" in params
    assert "context" in params
    assert "topic" not in params
    assert "envelope" not in params


def test_container_disabled_by_default_has_no_orchestrator() -> None:
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
    )
    assert settings.orchestrator.enabled is False
    container = build_container(settings, clock=FixedClock(OBSERVED_AT))
    assert container.market_data_orchestrator is None
    assert settings.safe_summary()["orchestrator"]["enabled"] is False
    assert "max_in_flight" in settings.safe_summary()["orchestrator"]


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
        trade_event(source_event_id="c-t1"),  # duplicate
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
    assert [key for _, key, _ in port.published] == [
        "market.trade",
        "market.quote",
        "market.bar",
    ]
    for ctx in results:
        assert ctx.audit[-1].decision is ctx.decision


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
    assert container.market_data_orchestrator.metrics.published == 0
