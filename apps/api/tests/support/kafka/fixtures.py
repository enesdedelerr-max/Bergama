"""Compact broker-free event runtime harness for tests."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.events.envelope import EventEnvelope
from app.events.retry import RetryPolicy
from app.events.topics import KafkaTopic, TopicRegistry
from app.events.worker import ConsumerWorker
from tests.support.kafka.broker import InMemoryEventBroker
from tests.support.kafka.consumer import FakeEventConsumer
from tests.support.kafka.dlq import FakeDlqPublisher
from tests.support.kafka.producer import FakeEventProducer


@dataclass
class RecordingHandler:
    """Test handler that can fail a configured number of times."""

    fail_times: int = 0
    calls: int = 0
    events: list[EventEnvelope] = field(default_factory=list)

    async def handle(self, event: EventEnvelope) -> None:
        self.calls += 1
        self.events.append(event)
        if self.calls <= self.fail_times:
            raise RuntimeError("handler boom")


@dataclass
class EventRuntimeHarness:
    broker: InMemoryEventBroker
    registry: TopicRegistry
    producer: FakeEventProducer
    consumer: FakeEventConsumer
    handler: RecordingHandler
    worker: ConsumerWorker
    dlq: FakeDlqPublisher | None
    stop_order: list[str] = field(default_factory=list)

    async def start(self) -> None:
        await self.producer.start()
        await self.consumer.start()
        self.worker.start()

    async def stop(self) -> None:
        await self.worker.stop()
        self.stop_order.append("worker")
        await self.consumer.stop()
        self.stop_order.append("consumer")
        await self.producer.stop()
        self.stop_order.append("producer")


@asynccontextmanager
async def event_runtime_harness(
    *,
    topics: list[str] | None = None,
    partitions: int = 1,
    group_id: str = "test-group",
    fail_times: int = 0,
    max_attempts: int = 3,
    with_dlq: bool = False,
    dlq_fail: bool = False,
) -> AsyncIterator[EventRuntimeHarness]:
    """Assemble an isolated broker + producer + consumer + worker."""
    broker = InMemoryEventBroker()
    registry = TopicRegistry()
    topic_names = topics or [KafkaTopic.EVENTS.value]
    for name in topic_names:
        broker.create_topic(name, partitions=partitions)
    producer = FakeEventProducer(
        broker,
        registry,
        clock=datetime(2026, 7, 12, 12, 0, 0, tzinfo=UTC),
    )
    consumer = FakeEventConsumer(
        broker,
        group_id=group_id,
        topics=topic_names,
        topic_registry=registry,
        poll_interval_seconds=0.005,
    )
    handler = RecordingHandler(fail_times=fail_times)
    dlq = FakeDlqPublisher(fail=dlq_fail) if with_dlq else None

    async def sleeper(_delay: float) -> None:
        return None

    worker = ConsumerWorker(
        consumer=consumer,
        handler=handler,
        retry_policy=RetryPolicy(
            max_attempts=max_attempts,
            initial_delay_seconds=0.0,
            max_delay_seconds=0.0,
            multiplier=1.0,
        ),
        dlq=dlq,
        sleeper=sleeper,
        name="harness",
    )
    harness = EventRuntimeHarness(
        broker=broker,
        registry=registry,
        producer=producer,
        consumer=consumer,
        handler=handler,
        worker=worker,
        dlq=dlq,
    )
    await harness.start()
    try:
        yield harness
    finally:
        await harness.stop()
