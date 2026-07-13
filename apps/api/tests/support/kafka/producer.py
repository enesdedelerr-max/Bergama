"""Test-only EventProducer backed by InMemoryEventBroker."""

from __future__ import annotations

from datetime import UTC, datetime

from app.events.envelope import EventEnvelope
from app.events.errors import KafkaNotConfiguredError, KafkaPublishFailedError
from app.events.ports import PublishResult
from app.events.serialization import serialize_event
from app.events.topics import KafkaTopic, TopicRegistry
from tests.support.kafka.broker import InMemoryEventBroker


class FakeEventProducer:
    """Implements EventProducer for broker-free tests."""

    def __init__(
        self,
        broker: InMemoryEventBroker,
        topic_registry: TopicRegistry | None = None,
        *,
        clock: datetime | None = None,
    ) -> None:
        self._broker = broker
        self._topics = topic_registry or TopicRegistry()
        self._started = False
        self._fixed_clock = clock

    @property
    def started(self) -> bool:
        return self._started

    async def start(self) -> None:
        if self._started:
            return
        self._started = True

    async def stop(self) -> None:
        self._started = False

    async def publish(
        self,
        topic: KafkaTopic,
        event: EventEnvelope,
        *,
        key: str | bytes | None = None,
    ) -> PublishResult:
        if not self._started:
            raise KafkaNotConfiguredError("fake producer is not started")
        topic_name = self._topics.resolve(topic)
        if not self._broker.has_topic(topic_name):
            raise KafkaPublishFailedError(f"unknown topic: {topic_name}")
        body = serialize_event(event)
        if key is None:
            encoded_key: bytes | None = str(event.idempotency_key).encode("utf-8")
        elif isinstance(key, bytes):
            encoded_key = key
        else:
            encoded_key = key.encode("utf-8")
        ts = self._fixed_clock or datetime.now(UTC)
        record = self._broker.publish(
            topic_name,
            value=body,
            key=encoded_key,
            timestamp=ts,
        )
        return PublishResult(
            topic=record.topic,
            partition=record.partition,
            offset=record.offset,
            timestamp=record.timestamp,
        )
