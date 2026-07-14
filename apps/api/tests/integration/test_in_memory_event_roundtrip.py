"""Broker-free round-trip integration using the in-memory harness."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.events.envelope import EventEnvelope
from app.events.errors import EventRetryExhaustedError
from app.events.topics import KafkaTopic
from tests.support.kafka import FakeDlqPublisher
from tests.support.kafka.fixtures import event_runtime_harness


async def _wait_until(predicate, *, timeout: float = 1.0) -> None:
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        if predicate():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("condition not met before timeout")


def _event(*, idem: str = "idem-1") -> EventEnvelope:
    return EventEnvelope(
        event_id=uuid4(),
        event_type="test.event",
        schema_version="1",
        source_system="test",
        occurred_at=datetime(2026, 7, 12, tzinfo=UTC),
        ingested_at=datetime(2026, 7, 12, tzinfo=UTC),
        idempotency_key=idem,
        payload={"symbol": "AAPL"},
        correlation_id="corr-rt",
        causation_id="cause-rt",
    )


@pytest.mark.asyncio
async def test_producer_broker_consumer_round_trip() -> None:
    async with event_runtime_harness() as harness:
        published = await harness.producer.publish(KafkaTopic.EVENTS, _event())
        await _wait_until(lambda: harness.handler.calls >= 1)
        handled = harness.handler.events[0]
        assert handled.correlation_id == "corr-rt"
        assert handled.causation_id == "cause-rt"
        assert published.offset == 0
        assert (
            harness.broker.committed_offset(group_id="test-group", topic="events", partition=0) == 1
        )


@pytest.mark.asyncio
async def test_retry_then_success_commits() -> None:
    async with event_runtime_harness(fail_times=2, max_attempts=3) as harness:
        await harness.producer.publish(KafkaTopic.EVENTS, _event())
        await _wait_until(lambda: harness.handler.calls == 3)
        assert (
            harness.broker.committed_offset(group_id="test-group", topic="events", partition=0) == 1
        )


@pytest.mark.asyncio
async def test_retry_exhaustion_no_dlq_no_commit() -> None:
    async with event_runtime_harness(fail_times=99, max_attempts=2) as harness:
        await harness.producer.publish(KafkaTopic.EVENTS, _event())
        task = harness.worker.task
        assert task is not None
        with pytest.raises(EventRetryExhaustedError):
            await task
        assert (
            harness.broker.committed_offset(group_id="test-group", topic="events", partition=0) == 0
        )


@pytest.mark.asyncio
async def test_retry_exhaustion_with_test_dlq_still_no_commit() -> None:
    async with event_runtime_harness(fail_times=99, max_attempts=2, with_dlq=True) as harness:
        await harness.producer.publish(KafkaTopic.EVENTS, _event())
        task = harness.worker.task
        assert task is not None
        with pytest.raises(EventRetryExhaustedError):
            await task
        assert harness.dlq is not None
        assert len(harness.dlq.failures) == 1
        assert (
            harness.broker.committed_offset(group_id="test-group", topic="events", partition=0) == 0
        )


@pytest.mark.asyncio
async def test_dlq_failure_no_commit() -> None:
    async with event_runtime_harness(
        fail_times=99, max_attempts=1, with_dlq=True, dlq_fail=True
    ) as harness:
        await harness.producer.publish(KafkaTopic.EVENTS, _event())
        task = harness.worker.task
        assert task is not None
        with pytest.raises(EventRetryExhaustedError):
            await task
        assert (
            harness.broker.committed_offset(group_id="test-group", topic="events", partition=0) == 0
        )


@pytest.mark.asyncio
async def test_graceful_full_runtime_shutdown_order() -> None:
    async with event_runtime_harness() as harness:
        await harness.producer.publish(KafkaTopic.EVENTS, _event())
        await _wait_until(lambda: harness.handler.calls >= 1)
    assert harness.stop_order == ["worker", "consumer", "producer"]
    task = harness.worker.task
    assert task is None or task.done()


@pytest.mark.asyncio
async def test_multi_group_replay_behavior() -> None:
    from tests.support.kafka.broker import InMemoryEventBroker
    from tests.support.kafka.consumer import FakeEventConsumer
    from tests.support.kafka.producer import FakeEventProducer

    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=1)
    producer = FakeEventProducer(broker)
    g1 = FakeEventConsumer(broker, group_id="alpha", topics=["events"])
    g2 = FakeEventConsumer(broker, group_id="beta", topics=["events"])
    await producer.start()
    await g1.start()
    await g2.start()
    await producer.publish(KafkaTopic.EVENTS, _event())
    a = await g1.get()
    b = await g2.get()
    assert a.envelope.event_id == b.envelope.event_id
    await g1.commit(a)
    assert broker.committed_offset(group_id="alpha", topic="events", partition=0) == 1
    assert broker.committed_offset(group_id="beta", topic="events", partition=0) == 0
    await g2.stop()
    await g1.stop()
    await producer.stop()


@pytest.mark.asyncio
async def test_separate_app_containers_do_not_share_kafka_runtime() -> None:
    s1 = AppSettings(environment=AppEnvironment.TEST, bootstrap_auth_enabled=False)
    s2 = AppSettings(environment=AppEnvironment.TEST, bootstrap_auth_enabled=False)
    c1 = build_container(s1)
    c2 = build_container(s2)
    assert c1.kafka_runtime is None
    assert c2.kafka_runtime is None
    assert c1 is not c2


@pytest.mark.asyncio
async def test_fake_dlq_captures_and_can_fail() -> None:
    dlq = FakeDlqPublisher(fail=False)
    assert dlq.failures == []
    failing = FakeDlqPublisher(fail=True)
    from app.events.errors import DlqUnavailableError, EventProcessingError
    from app.events.ports import ConsumedEvent

    event = _event()
    consumed = ConsumedEvent(
        envelope=event,
        topic="events",
        partition=0,
        offset=0,
        timestamp=None,
        key=None,
        headers={},
    )
    with pytest.raises(DlqUnavailableError):
        await failing.publish_failed(consumed, EventProcessingError("x"), 2)
