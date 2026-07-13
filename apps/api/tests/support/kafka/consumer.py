"""Test-only EventConsumer backed by InMemoryEventBroker."""

from __future__ import annotations

import asyncio

from app.events.errors import EventDeserializationError, KafkaNotConfiguredError
from app.events.ports import ConsumedEvent
from app.events.serialization import deserialize_event
from app.events.topics import TopicRegistry
from tests.support.kafka.broker import BrokerRecord, InMemoryEventBroker


class FakeEventConsumer:
    """Implements EventConsumer. One active consumer per group is assumed."""

    def __init__(
        self,
        broker: InMemoryEventBroker,
        *,
        group_id: str,
        topics: list[str],
        topic_registry: TopicRegistry | None = None,
        poll_interval_seconds: float = 0.01,
    ) -> None:
        if not group_id.strip():
            msg = "group_id is required"
            raise ValueError(msg)
        if not topics:
            msg = "topics must be non-empty"
            raise ValueError(msg)
        self._broker = broker
        self._group_id = group_id
        self._registry = topic_registry or TopicRegistry()
        self._topic_names = self._registry.resolve_many(topics)
        self._poll_interval = poll_interval_seconds
        self._started = False
        self._scan_index = 0

    @property
    def started(self) -> bool:
        return self._started

    @property
    def group_id(self) -> str:
        return self._group_id

    async def start(self) -> None:
        if self._started:
            return
        for topic in self._topic_names:
            if not self._broker.has_topic(topic):
                msg = f"unknown topic: {topic}"
                raise KafkaNotConfiguredError(msg)
        self._started = True

    async def stop(self) -> None:
        self._started = False

    async def get(self) -> ConsumedEvent:
        if not self._started:
            raise KafkaNotConfiguredError("fake consumer is not started")
        while True:
            record = self._next_record()
            if record is not None:
                try:
                    envelope = deserialize_event(record.value)
                except Exception as exc:
                    raise EventDeserializationError("event deserialization failed") from exc
                return ConsumedEvent(
                    envelope=envelope,
                    topic=record.topic,
                    partition=record.partition,
                    offset=record.offset,
                    timestamp=record.timestamp,
                    key=record.key,
                    headers=dict(record.headers),
                )
            await asyncio.sleep(self._poll_interval)

    async def commit(self, event: ConsumedEvent) -> None:
        if not self._started:
            raise KafkaNotConfiguredError("fake consumer is not started")
        self._broker.commit(
            group_id=self._group_id,
            topic=event.topic,
            partition=event.partition,
            next_offset=event.offset + 1,
        )

    def _partition_pairs(self) -> list[tuple[str, int]]:
        pairs: list[tuple[str, int]] = []
        for topic in self._topic_names:
            count = self._broker.partition_count(topic)
            for partition in range(count):
                pairs.append((topic, partition))
        return pairs

    def _next_record(self) -> BrokerRecord | None:
        pairs = self._partition_pairs()
        if not pairs:
            return None
        start = self._scan_index % len(pairs)
        for step in range(len(pairs)):
            topic, partition = pairs[(start + step) % len(pairs)]
            record = self._broker.read(
                group_id=self._group_id,
                topic=topic,
                partition=partition,
            )
            if record is not None:
                self._scan_index = (start + step + 1) % len(pairs)
                return record
        return None
