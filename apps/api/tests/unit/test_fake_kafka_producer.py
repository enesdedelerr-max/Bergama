"""Unit tests for FakeEventProducer."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.events.envelope import EventEnvelope
from app.events.errors import KafkaNotConfiguredError, KafkaPublishFailedError
from app.events.topics import KafkaTopic, TopicRegistry
from tests.support.kafka.broker import InMemoryEventBroker
from tests.support.kafka.producer import FakeEventProducer


def _event(**overrides: object) -> EventEnvelope:
    data: dict[str, object] = {
        "event_id": uuid4(),
        "event_type": "test.event",
        "schema_version": "1",
        "source_system": "test",
        "occurred_at": datetime(2026, 7, 12, tzinfo=UTC),
        "ingested_at": datetime(2026, 7, 12, tzinfo=UTC),
        "idempotency_key": "idem",
        "payload": {"a": 1},
    }
    data.update(overrides)
    return EventEnvelope.model_validate(data)


@pytest.mark.asyncio
async def test_producer_implements_event_producer_protocol() -> None:
    from typing import cast

    from app.events.ports import EventProducer

    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=1)
    producer = FakeEventProducer(broker)
    typed: EventProducer = cast(EventProducer, producer)
    await typed.start()
    await typed.stop()


@pytest.mark.asyncio
async def test_producer_requires_start() -> None:
    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=1)
    producer = FakeEventProducer(broker)
    with pytest.raises(KafkaNotConfiguredError):
        await producer.publish(KafkaTopic.EVENTS, _event())


@pytest.mark.asyncio
async def test_producer_unknown_topic_fails() -> None:
    broker = InMemoryEventBroker()
    producer = FakeEventProducer(broker)
    await producer.start()
    with pytest.raises(KafkaPublishFailedError):
        await producer.publish(KafkaTopic.EVENTS, _event())


@pytest.mark.asyncio
async def test_producer_lifecycle_idempotent() -> None:
    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=1)
    producer = FakeEventProducer(broker)
    await producer.start()
    await producer.start()
    assert producer.started is True
    await producer.stop()
    await producer.stop()
    assert producer.started is False


@pytest.mark.asyncio
async def test_producer_publish_result() -> None:
    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=1)
    producer = FakeEventProducer(
        broker,
        TopicRegistry(),
        clock=datetime(2026, 7, 12, 12, 0, 0, tzinfo=UTC),
    )
    await producer.start()
    result = await producer.publish(KafkaTopic.EVENTS, _event())
    assert result.topic == "events"
    assert result.partition == 0
    assert result.offset == 0
    assert result.timestamp is not None
