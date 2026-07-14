"""Adapter-focused tests at the aiokafka boundary (mocked)."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.core.kafka_settings import KafkaSettings
from app.events.envelope import EventEnvelope
from app.events.topics import KafkaTopic, TopicRegistry
from app.infrastructure.kafka.consumer import AiokafkaEventConsumer
from app.infrastructure.kafka.producer import AiokafkaEventProducer


def _settings() -> KafkaSettings:
    return KafkaSettings(
        enabled=True,
        bootstrap_servers=["localhost:9092"],
        producer_enabled=True,
        consumer_enabled=True,
        enable_auto_commit=False,
    )


def _event() -> EventEnvelope:
    return EventEnvelope(
        event_id=uuid4(),
        event_type="test.event",
        schema_version="1",
        source_system="test",
        occurred_at=datetime(2026, 7, 12, tzinfo=UTC),
        ingested_at=datetime(2026, 7, 12, tzinfo=UTC),
        idempotency_key="idem",
        payload={"a": 1},
    )


@pytest.mark.asyncio
async def test_normalized_publish_result() -> None:
    registry = TopicRegistry()
    fake = MagicMock()
    fake.start = AsyncMock()
    fake.stop = AsyncMock()
    fake.send_and_wait = AsyncMock(
        return_value=SimpleNamespace(partition=2, offset=99, timestamp=1_700_000_000_000)
    )
    producer = AiokafkaEventProducer(_settings(), registry, producer_factory=lambda **_: fake)
    await producer.start()
    result = await producer.publish(KafkaTopic.EVENTS, _event())
    assert result.topic == "events"
    assert result.partition == 2
    assert result.offset == 99
    assert result.timestamp is not None
    await producer.stop()


@pytest.mark.asyncio
async def test_consumed_message_mapping_and_manual_commit() -> None:
    from app.events.serialization import serialize_event

    registry = TopicRegistry()
    event = _event()
    body = serialize_event(event)
    message = SimpleNamespace(
        value=body,
        topic="events",
        partition=1,
        offset=7,
        timestamp=1_700_000_000_000,
        key=b"k",
        headers=(("h", b"v"),),
    )
    fake = MagicMock()
    fake.start = AsyncMock()
    fake.stop = AsyncMock()
    fake.getone = AsyncMock(return_value=message)
    fake.commit = AsyncMock()
    consumer = AiokafkaEventConsumer(
        _settings(),
        registry,
        topics=["events"],
        consumer_factory=lambda *a, **k: fake,
    )
    await consumer.start()
    consumed = await consumer.get()
    assert consumed.envelope.event_id == event.event_id
    assert consumed.partition == 1
    assert consumed.offset == 7
    await consumer.commit(consumed)
    fake.commit.assert_awaited()
    await consumer.stop()


@pytest.mark.asyncio
async def test_consumer_lifecycle_idempotent() -> None:
    registry = TopicRegistry()
    fake = MagicMock()
    fake.start = AsyncMock()
    fake.stop = AsyncMock()
    consumer = AiokafkaEventConsumer(
        _settings(),
        registry,
        topics=["events"],
        consumer_factory=lambda *a, **k: fake,
    )
    await consumer.start()
    await consumer.start()
    assert fake.start.await_count == 1
    await consumer.stop()
    await consumer.stop()
    assert fake.stop.await_count == 1
