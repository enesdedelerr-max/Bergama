"""In-memory Kafka integration for KafkaPublishAdapter + orchestrator (#306)."""

from __future__ import annotations

import asyncio

import pytest
from app.core.clock import FixedClock
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.core.kafka_settings import KafkaSettings
from app.core.orchestrator_settings import OrchestratorSettings
from app.core.secrets import SecretSettings
from app.events.serialization import deserialize_event
from app.events.topics import KafkaTopic, TopicRegistry
from app.infrastructure.kafka.market_data_publish import KafkaPublishAdapter
from app.infrastructure.kafka.runtime import KafkaRuntime
from app.market_data.keys import build_idempotency_key
from app.market_data.orchestrator.errors import OrchestratorConfigurationError
from app.market_data.orchestrator.pipeline import build_market_data_orchestrator
from app.market_data.orchestrator.policies import PipelineDecision
from app.market_data.orchestrator.routing import routing_key_for
from app.market_data.serialization import market_event_from_payload
from tests.conftest import VALID_PROD_JWT_SECRET
from tests.support.kafka.broker import InMemoryEventBroker
from tests.support.kafka.producer import FakeEventProducer
from tests.support.market_data_fixtures import (
    make_bar,
    make_filing,
    make_fundamental,
    make_macro,
    make_news,
    make_quote,
    make_trade,
    source,
)
from tests.support.provider_contracts.clocks import OBSERVED_AT


def _all_records(broker: InMemoryEventBroker, topic: str) -> list[object]:
    records: list[object] = []
    for partition in range(broker.partition_count(topic)):
        records.extend(broker.records(topic, partition))
    return records


def _settings(**overrides: object) -> AppSettings:
    base: dict[str, object] = {
        "environment": AppEnvironment.TEST,
        "bootstrap_auth_enabled": True,
        "secrets": SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        "kafka": KafkaSettings(enabled=False),
        "orchestrator": OrchestratorSettings(enabled=False),
    }
    base.update(overrides)
    return AppSettings(**base)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_representative_events_publish_offline() -> None:
    clock = FixedClock(OBSERVED_AT)
    broker = InMemoryEventBroker()
    registry = TopicRegistry()
    topic = registry.resolve(KafkaTopic.MARKET_DATA)
    broker.create_topic(topic, partitions=3)
    producer = FakeEventProducer(broker, registry, clock=OBSERVED_AT)
    await producer.start()
    adapter = KafkaPublishAdapter(producer=producer, topic_registry=registry, clock=clock)
    orch = build_market_data_orchestrator(
        OrchestratorSettings(enabled=True, max_in_flight=16),
        clock=clock,
        publish_port=adapter,
    )

    events = [
        make_bar(source=source(provider="polygon", source_event_id="poly-bar-1")),
        make_trade(source=source(provider="polygon", source_event_id="poly-trade-1")),
        make_quote(source=source(provider="polygon", source_event_id="poly-quote-1")),
        make_fundamental(source=source(provider="finnhub", source_event_id="fh-fund-1")),
        make_macro(source=source(provider="fred", source_event_id="fred-macro-1")),
        make_filing(source=source(provider="sec_edgar", source_event_id="sec-filing-1")),
        make_news(source=source(provider="benzinga", source_event_id="bz-news-1")),
    ]
    results = await orch.process_batch(events, correlation_id="offline-306")
    assert [r.decision for r in results] == [PipelineDecision.PUBLISHED] * len(events)

    records = _all_records(broker, topic)
    assert len(records) == len(events)
    by_key = {record.key: record for record in records}  # type: ignore[union-attr]
    for event in events:
        key = build_idempotency_key(event).encode("utf-8")
        record = by_key[key]
        assert record.topic == "market-data"  # type: ignore[union-attr]
        envelope = deserialize_event(record.value)  # type: ignore[union-attr]
        assert envelope.correlation_id == "offline-306"
        assert envelope.event_type == f"market.{event.event_type.value}"
        assert market_event_from_payload(envelope.payload).event_type is event.event_type


@pytest.mark.asyncio
async def test_publish_failure_does_not_poison_dedup() -> None:
    clock = FixedClock(OBSERVED_AT)
    broker = InMemoryEventBroker()
    registry = TopicRegistry()
    # Topic missing → FakeEventProducer fails
    producer = FakeEventProducer(broker, registry, clock=OBSERVED_AT)
    await producer.start()
    adapter = KafkaPublishAdapter(producer=producer, topic_registry=registry, clock=clock)
    orch = build_market_data_orchestrator(
        OrchestratorSettings(enabled=True),
        clock=clock,
        publish_port=adapter,
    )
    event = make_trade(source=source(source_event_id="retry-306"))
    failed = await orch.process(event)
    assert failed.decision is PipelineDecision.PUBLISH_FAILED

    broker.create_topic(registry.resolve(KafkaTopic.MARKET_DATA))
    ok = await orch.process(event)
    assert ok.decision is PipelineDecision.PUBLISHED
    suppressed = await orch.process(event)
    assert suppressed.decision is PipelineDecision.DUPLICATE_SUPPRESSED


@pytest.mark.asyncio
async def test_concurrent_same_key_publishes_at_most_once() -> None:
    clock = FixedClock(OBSERVED_AT)
    broker = InMemoryEventBroker()
    registry = TopicRegistry()
    topic = registry.resolve(KafkaTopic.MARKET_DATA)
    broker.create_topic(topic)
    producer = FakeEventProducer(broker, registry, clock=OBSERVED_AT)
    await producer.start()

    entered = asyncio.Event()
    release = asyncio.Event()

    class GatedProducer(FakeEventProducer):
        async def publish(self, topic, event, *, key=None):  # type: ignore[no-untyped-def]
            entered.set()
            await release.wait()
            return await super().publish(topic, event, key=key)

    gated = GatedProducer(broker, registry, clock=OBSERVED_AT)
    await gated.start()
    adapter = KafkaPublishAdapter(producer=gated, topic_registry=registry, clock=clock)
    orch = build_market_data_orchestrator(
        OrchestratorSettings(enabled=True, max_in_flight=4, admission_timeout_seconds=1.0),
        clock=clock,
        publish_port=adapter,
    )
    event = make_trade(source=source(source_event_id="race-306"))

    t1 = asyncio.create_task(orch.process(event))
    await entered.wait()
    t2 = asyncio.create_task(orch.process(event))
    release.set()
    first = await t1
    second = await t2
    assert {first.decision, second.decision} == {
        PipelineDecision.PUBLISHED,
        PipelineDecision.DUPLICATE_SUPPRESSED,
    }
    assert len(_all_records(broker, topic)) == 1


def test_kafka_mode_requires_kafka_producer() -> None:
    with pytest.raises(OrchestratorConfigurationError, match="kafka_publish_unavailable"):
        build_container(
            _settings(
                orchestrator=OrchestratorSettings(enabled=True, publish_backend="kafka"),
                kafka=KafkaSettings(enabled=False),
            ),
            clock=FixedClock(OBSERVED_AT),
        )


def test_dry_run_does_not_require_or_build_kafka_adapter() -> None:
    container = build_container(
        _settings(orchestrator=OrchestratorSettings(enabled=True, dry_run=True)),
        clock=FixedClock(OBSERVED_AT),
    )
    assert container.market_data_orchestrator is not None
    assert container.kafka_runtime is None
    assert not isinstance(container.market_data_orchestrator.publish_port, KafkaPublishAdapter)


def test_kafka_enabled_alone_does_not_select_kafka_publish() -> None:
    """Enabling Kafka does not silently wire the market-data publish adapter."""
    with pytest.raises(OrchestratorConfigurationError, match="publish_port_required"):
        build_container(
            _settings(
                orchestrator=OrchestratorSettings(enabled=True, publish_backend="none"),
                kafka=KafkaSettings(
                    enabled=True,
                    bootstrap_servers=["localhost:9092"],
                    producer_enabled=True,
                    consumer_enabled=False,
                ),
            ),
            clock=FixedClock(OBSERVED_AT),
        )


@pytest.mark.asyncio
async def test_container_kafka_mode_wires_adapter_and_closes_orchestrator_first(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    order: list[str] = []
    clock = FixedClock(OBSERVED_AT)
    broker = InMemoryEventBroker()
    registry = TopicRegistry()
    broker.create_topic(registry.resolve(KafkaTopic.MARKET_DATA))

    class TrackingProducer(FakeEventProducer):
        async def stop(self) -> None:
            order.append("kafka_producer")
            await super().stop()

    tracking = TrackingProducer(broker, registry, clock=OBSERVED_AT)
    runtime = KafkaRuntime(
        settings=KafkaSettings(
            enabled=True,
            bootstrap_servers=["localhost:9092"],
            producer_enabled=True,
            consumer_enabled=False,
        ),
        topic_registry=registry,
        producer=tracking,  # type: ignore[arg-type]
        consumers=[],
        workers=[],
    )
    await runtime.start()

    container = build_container(
        _settings(
            orchestrator=OrchestratorSettings(enabled=True, publish_backend="kafka"),
            kafka=KafkaSettings(
                enabled=True,
                bootstrap_servers=["localhost:9092"],
                producer_enabled=True,
                consumer_enabled=False,
            ),
        ),
        clock=clock,
        kafka_runtime=runtime,
    )
    assert container.market_data_orchestrator is not None
    assert isinstance(container.market_data_orchestrator.publish_port, KafkaPublishAdapter)

    from app.market_data.orchestrator.pipeline import MarketDataOrchestrator

    original_aclose = MarketDataOrchestrator.aclose

    async def tracking_aclose(self: MarketDataOrchestrator) -> None:
        if self is container.market_data_orchestrator:
            order.append("orchestrator")
        await original_aclose(self)

    monkeypatch.setattr(MarketDataOrchestrator, "aclose", tracking_aclose)

    event = make_trade(source=source(source_event_id="wired-306"))
    published = await container.market_data_orchestrator.process(event)
    assert published.decision is PipelineDecision.PUBLISHED
    assert routing_key_for(event).startswith("market.")

    await container.aclose()
    assert order[:2] == ["orchestrator", "kafka_producer"]
    assert container.market_data_orchestrator.closed is True
    assert tracking.started is False


@pytest.mark.asyncio
async def test_no_startup_publish_with_kafka_mode() -> None:
    broker = InMemoryEventBroker()
    registry = TopicRegistry()
    broker.create_topic(registry.resolve(KafkaTopic.MARKET_DATA))
    producer = FakeEventProducer(broker, registry, clock=OBSERVED_AT)
    runtime = KafkaRuntime(
        settings=KafkaSettings(
            enabled=True,
            bootstrap_servers=["localhost:9092"],
            producer_enabled=True,
            consumer_enabled=False,
        ),
        topic_registry=registry,
        producer=producer,  # type: ignore[arg-type]
        consumers=[],
        workers=[],
    )
    await runtime.start()
    build_container(
        _settings(
            orchestrator=OrchestratorSettings(enabled=True, publish_backend="kafka"),
            kafka=KafkaSettings(
                enabled=True,
                bootstrap_servers=["localhost:9092"],
                producer_enabled=True,
                consumer_enabled=False,
            ),
        ),
        clock=FixedClock(OBSERVED_AT),
        kafka_runtime=runtime,
    )
    assert _all_records(broker, registry.resolve(KafkaTopic.MARKET_DATA)) == []
    await runtime.stop()
