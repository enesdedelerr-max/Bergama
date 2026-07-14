"""Unit tests for FakeEventConsumer."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.events.envelope import EventEnvelope
from app.events.errors import EventDeserializationError, KafkaNotConfiguredError
from app.events.serialization import serialize_event
from app.events.topics import KafkaTopic
from tests.support.kafka.broker import InMemoryEventBroker
from tests.support.kafka.consumer import FakeEventConsumer
from tests.support.kafka.producer import FakeEventProducer


def _event(*, key: str = "idem") -> EventEnvelope:
    return EventEnvelope(
        event_id=uuid4(),
        event_type="test.event",
        schema_version="1",
        source_system="test",
        occurred_at=datetime(2026, 7, 12, tzinfo=UTC),
        ingested_at=datetime(2026, 7, 12, tzinfo=UTC),
        idempotency_key=key,
        payload={"a": 1},
        correlation_id="corr-1",
        causation_id="cause-1",
    )


@pytest.mark.asyncio
async def test_consumer_implements_event_consumer_protocol() -> None:
    from typing import cast

    from app.events.ports import EventConsumer

    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=1)
    consumer = FakeEventConsumer(broker, group_id="g1", topics=["events"])
    typed: EventConsumer = cast(EventConsumer, consumer)
    await typed.start()
    await typed.stop()


@pytest.mark.asyncio
async def test_consumer_requires_start() -> None:
    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=1)
    consumer = FakeEventConsumer(broker, group_id="g1", topics=["events"])
    with pytest.raises(KafkaNotConfiguredError):
        await consumer.get()


@pytest.mark.asyncio
async def test_consumer_lifecycle_idempotent() -> None:
    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=1)
    consumer = FakeEventConsumer(broker, group_id="g1", topics=["events"])
    await consumer.start()
    await consumer.start()
    assert consumer.started is True
    await consumer.stop()
    await consumer.stop()
    assert consumer.started is False


@pytest.mark.asyncio
async def test_manual_commit_tracking() -> None:
    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=1)
    producer = FakeEventProducer(broker)
    consumer = FakeEventConsumer(broker, group_id="g1", topics=["events"])
    await producer.start()
    await consumer.start()
    await producer.publish(KafkaTopic.EVENTS, _event())
    consumed = await consumer.get()
    assert broker.committed_offset(group_id="g1", topic="events", partition=0) == 0
    await consumer.commit(consumed)
    assert broker.committed_offset(group_id="g1", topic="events", partition=0) == 1


@pytest.mark.asyncio
async def test_independent_consumer_groups() -> None:
    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=1)
    producer = FakeEventProducer(broker)
    c1 = FakeEventConsumer(broker, group_id="g1", topics=["events"])
    c2 = FakeEventConsumer(broker, group_id="g2", topics=["events"])
    await producer.start()
    await c1.start()
    await c2.start()
    await producer.publish(KafkaTopic.EVENTS, _event())
    e1 = await c1.get()
    e2 = await c2.get()
    assert e1.envelope.event_id == e2.envelope.event_id
    await c1.commit(e1)
    assert broker.committed_offset(group_id="g1", topic="events", partition=0) == 1
    assert broker.committed_offset(group_id="g2", topic="events", partition=0) == 0


@pytest.mark.asyncio
async def test_topic_isolation() -> None:
    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=1)
    broker.create_topic("audit", partitions=1)
    producer = FakeEventProducer(broker)
    consumer = FakeEventConsumer(broker, group_id="g1", topics=["audit"])
    await producer.start()
    await consumer.start()
    await producer.publish(KafkaTopic.EVENTS, _event())
    # No audit events: get would hang; publish audit then consume.
    await producer.publish(KafkaTopic.AUDIT, _event(key="audit-1"))
    consumed = await consumer.get()
    assert consumed.topic == "audit"


@pytest.mark.asyncio
async def test_partition_ordering() -> None:
    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=1)
    producer = FakeEventProducer(broker)
    consumer = FakeEventConsumer(broker, group_id="g1", topics=["events"])
    await producer.start()
    await consumer.start()
    for i in range(3):
        await producer.publish(KafkaTopic.EVENTS, _event(key=f"k-{i}"))
    offsets = []
    for _ in range(3):
        item = await consumer.get()
        offsets.append(item.offset)
        await consumer.commit(item)
    assert offsets == [0, 1, 2]


@pytest.mark.asyncio
async def test_malformed_event_rejected() -> None:
    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=1)
    broker.publish("events", value=b"not-json")
    consumer = FakeEventConsumer(broker, group_id="g1", topics=["events"])
    await consumer.start()
    with pytest.raises(EventDeserializationError):
        await consumer.get()


@pytest.mark.asyncio
async def test_content_hash_verified_on_consume() -> None:
    import json

    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=1)
    event = _event()
    payload = json.loads(serialize_event(event).decode("utf-8"))
    payload["content_hash"] = "0" * 64
    broker.publish(
        "events",
        value=json.dumps(payload, separators=(",", ":"), sort_keys=True).encode(),
    )
    consumer = FakeEventConsumer(broker, group_id="g1", topics=["events"])
    await consumer.start()
    with pytest.raises(EventDeserializationError):
        await consumer.get()
