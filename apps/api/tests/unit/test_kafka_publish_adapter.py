"""Unit tests for KafkaPublishAdapter (#306)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from app.core.clock import FixedClock
from app.events.errors import KafkaNotConfiguredError, KafkaPublishFailedError
from app.events.ports import PublishResult as KafkaPublishResult
from app.events.serialization import deserialize_event
from app.events.topics import KafkaTopic, TopicRegistry
from app.infrastructure.kafka.market_data_publish import (
    KafkaPublishAdapter,
    KafkaPublishIdempotencyMismatchError,
    KafkaPublishUnknownRouteError,
)
from app.market_data.enums import MarketEventType
from app.market_data.keys import build_idempotency_key
from app.market_data.orchestrator.context import PipelineContext
from app.market_data.orchestrator.policies import PipelineDecision
from app.market_data.orchestrator.ports import PublishResult
from app.market_data.orchestrator.routing import routing_key_for
from app.market_data.serialization import market_event_from_payload
from tests.support.kafka.broker import InMemoryEventBroker
from tests.support.kafka.producer import FakeEventProducer
from tests.support.market_data_fixtures import (
    make_bar,
    make_filing,
    make_fundamental,
    make_macro,
    make_news,
    make_quote,
    make_reference,
    make_trade,
    source,
)
from tests.support.provider_contracts.clocks import OBSERVED_AT

_CLOCK = FixedClock(OBSERVED_AT)


def _all_records(broker: InMemoryEventBroker, topic: str) -> list[object]:
    records: list[object] = []
    for partition in range(broker.partition_count(topic)):
        records.extend(broker.records(topic, partition))
    return records


def _context(event: object, *, correlation_id: str | None = "corr-1") -> PipelineContext:
    return PipelineContext(
        event=event,  # type: ignore[arg-type]
        dedup_key=f"dedup:{build_idempotency_key(event)}",  # type: ignore[arg-type]
        idempotency_key=build_idempotency_key(event),  # type: ignore[arg-type]
        routing_key=routing_key_for(event),  # type: ignore[arg-type]
        decision=PipelineDecision.ACCEPTED,
        quality=event.quality,  # type: ignore[attr-defined]
        received_at=_CLOCK.now(),
        pipeline_clock=_CLOCK,
        correlation_id=correlation_id,
        audit=(),
    )


@pytest.mark.asyncio
async def test_all_market_routes_map_to_market_data_topic() -> None:
    broker = InMemoryEventBroker()
    registry = TopicRegistry()
    broker.create_topic(registry.resolve(KafkaTopic.MARKET_DATA))
    producer = FakeEventProducer(broker, registry, clock=OBSERVED_AT)
    await producer.start()
    adapter = KafkaPublishAdapter(producer=producer, topic_registry=registry, clock=_CLOCK)

    factories = (
        make_quote,
        make_trade,
        make_bar,
        make_reference,
        make_fundamental,
        make_macro,
        make_filing,
        make_news,
    )
    for factory in factories:
        event = factory()
        result = await adapter.publish(
            event, routing_key=routing_key_for(event), context=_context(event)
        )
        assert result.succeeded is True
        assert result.idempotency_acknowledged is True
        assert result.safe_metadata["topic"] == "market-data"
        assert set(result.safe_metadata) == {"topic", "partition", "offset"}
        assert "payload" not in result.safe_metadata
        assert not hasattr(result, "topic")
        assert result.sink_message_id == (
            f"market-data:{result.safe_metadata['partition']}:{result.safe_metadata['offset']}"
        )

    records = _all_records(broker, "market-data")
    assert len(records) == len(factories)
    # Records may land on different partitions; match by idempotency key.
    by_key = {record.key: record for record in records}  # type: ignore[union-attr]
    for factory in factories:
        event = factory()
        key = build_idempotency_key(event).encode("utf-8")
        record = by_key[key]
        envelope = deserialize_event(record.value)  # type: ignore[union-attr]
        assert envelope.event_type == f"market.{event.event_type.value}"
        assert envelope.correlation_id == "corr-1"
        assert envelope.idempotency_key == build_idempotency_key(event)
        parsed = market_event_from_payload(envelope.payload)
        assert parsed.event_type is event.event_type


def test_approved_routing_keys_cover_all_event_types() -> None:
    expected = {f"market.{item.value}" for item in MarketEventType}
    assert KafkaPublishAdapter.approved_routing_keys() == expected


def test_unknown_routing_key_rejected() -> None:
    with pytest.raises(KafkaPublishUnknownRouteError, match="unknown market-data routing key"):
        KafkaPublishAdapter.topic_for_routing_key("provider.polygon.trade")


@pytest.mark.asyncio
async def test_context_idempotency_mismatch_fails_closed_without_publish() -> None:
    broker = InMemoryEventBroker()
    registry = TopicRegistry()
    broker.create_topic(registry.resolve(KafkaTopic.MARKET_DATA))
    producer = FakeEventProducer(broker, registry, clock=OBSERVED_AT)
    await producer.start()
    adapter = KafkaPublishAdapter(producer=producer, topic_registry=registry, clock=_CLOCK)
    event = make_trade(source=source(source_event_id="mismatch-1"))
    ctx = _context(event)
    bad = PipelineContext(
        event=event,
        dedup_key=ctx.dedup_key,
        idempotency_key="not-the-canonical-key",
        routing_key=ctx.routing_key,
        decision=ctx.decision,
        quality=ctx.quality,
        received_at=ctx.received_at,
        pipeline_clock=ctx.pipeline_clock,
        correlation_id=ctx.correlation_id,
        audit=(),
    )
    with pytest.raises(KafkaPublishIdempotencyMismatchError, match="does not match"):
        await adapter.publish(event, routing_key=routing_key_for(event), context=bad)
    assert _all_records(broker, "market-data") == []


@pytest.mark.asyncio
async def test_record_key_equals_idempotency_key() -> None:
    broker = InMemoryEventBroker()
    registry = TopicRegistry()
    broker.create_topic(registry.resolve(KafkaTopic.MARKET_DATA))
    producer = FakeEventProducer(broker, registry, clock=OBSERVED_AT)
    await producer.start()
    adapter = KafkaPublishAdapter(producer=producer, topic_registry=registry, clock=_CLOCK)
    event = make_trade(source=source(source_event_id="key-1"))
    ctx = _context(event)
    await adapter.publish(event, routing_key=ctx.routing_key or "", context=ctx)
    record = _all_records(broker, "market-data")[0]
    assert record.key == (ctx.idempotency_key or "").encode("utf-8")  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_topic_prefix_is_honored() -> None:
    broker = InMemoryEventBroker()
    registry = TopicRegistry(topic_prefix="dev.")
    topic_name = registry.resolve(KafkaTopic.MARKET_DATA)
    assert topic_name == "dev.market-data"
    broker.create_topic(topic_name)
    producer = FakeEventProducer(broker, registry, clock=OBSERVED_AT)
    await producer.start()
    adapter = KafkaPublishAdapter(producer=producer, topic_registry=registry, clock=_CLOCK)
    event = make_bar()
    result = await adapter.publish(
        event, routing_key=routing_key_for(event), context=_context(event)
    )
    assert result.safe_metadata["topic"] == "dev.market-data"
    assert result.succeeded is True


@pytest.mark.asyncio
async def test_producer_not_started_fails_closed() -> None:
    broker = InMemoryEventBroker()
    registry = TopicRegistry()
    broker.create_topic(registry.resolve(KafkaTopic.MARKET_DATA))
    producer = FakeEventProducer(broker, registry)
    adapter = KafkaPublishAdapter(producer=producer, topic_registry=registry, clock=_CLOCK)
    event = make_trade()
    with pytest.raises(KafkaNotConfiguredError):
        await adapter.publish(event, routing_key=routing_key_for(event), context=_context(event))


@pytest.mark.asyncio
async def test_missing_topic_maps_to_publish_failed() -> None:
    broker = InMemoryEventBroker()
    registry = TopicRegistry()
    producer = FakeEventProducer(broker, registry)
    await producer.start()
    adapter = KafkaPublishAdapter(producer=producer, topic_registry=registry, clock=_CLOCK)
    event = make_trade()
    with pytest.raises(KafkaPublishFailedError):
        await adapter.publish(event, routing_key=routing_key_for(event), context=_context(event))


@pytest.mark.asyncio
async def test_result_is_orchestrator_publish_result() -> None:
    broker = InMemoryEventBroker()
    registry = TopicRegistry()
    broker.create_topic(registry.resolve(KafkaTopic.MARKET_DATA))
    producer = FakeEventProducer(broker, registry, clock=datetime(2024, 1, 1, tzinfo=UTC))
    await producer.start()
    adapter = KafkaPublishAdapter(producer=producer, topic_registry=registry, clock=_CLOCK)
    event = make_quote()
    result = await adapter.publish(
        event, routing_key=routing_key_for(event), context=_context(event)
    )
    assert isinstance(result, PublishResult)
    assert not isinstance(result, KafkaPublishResult)
    assert set(PublishResult.__dataclass_fields__) == {
        "succeeded",
        "published_at",
        "sink_message_id",
        "idempotency_acknowledged",
        "safe_metadata",
    }


@pytest.mark.asyncio
async def test_envelope_preserves_decimal_strings() -> None:
    broker = InMemoryEventBroker()
    registry = TopicRegistry()
    broker.create_topic(registry.resolve(KafkaTopic.MARKET_DATA))
    producer = FakeEventProducer(broker, registry, clock=OBSERVED_AT)
    await producer.start()
    adapter = KafkaPublishAdapter(producer=producer, topic_registry=registry, clock=_CLOCK)
    event = make_trade(price=Decimal("10.500"))
    await adapter.publish(event, routing_key=routing_key_for(event), context=_context(event))
    envelope = deserialize_event(_all_records(broker, "market-data")[0].value)  # type: ignore[union-attr]
    assert envelope.payload["price"] == "10.5"
    assert envelope.event_id != UUID(int=0)
