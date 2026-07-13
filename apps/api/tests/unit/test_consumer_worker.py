"""Unit tests for consumer worker commit/retry/fail-closed semantics."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.events.envelope import EventEnvelope
from app.events.errors import DlqUnavailableError, EventProcessingError, EventRetryExhaustedError
from app.events.ports import ConsumedEvent
from app.events.retry import RetryPolicy
from app.events.worker import ConsumerWorker


def _envelope() -> EventEnvelope:
    return EventEnvelope(
        event_id=uuid4(),
        event_type="test.event",
        schema_version="1",
        source_system="test",
        occurred_at=datetime(2026, 7, 12, tzinfo=UTC),
        ingested_at=datetime(2026, 7, 12, tzinfo=UTC),
        idempotency_key="k1",
        payload={"ok": True},
    )


def _consumed() -> ConsumedEvent:
    return ConsumedEvent(
        envelope=_envelope(),
        topic="events",
        partition=0,
        offset=10,
        timestamp=None,
        key=None,
        headers={},
    )


@dataclass
class FakeConsumer:
    commits: list[ConsumedEvent] = field(default_factory=list)

    async def start(self) -> None:
        return None

    async def get(self) -> ConsumedEvent:
        raise TimeoutError

    async def commit(self, event: ConsumedEvent) -> None:
        self.commits.append(event)

    async def stop(self) -> None:
        return None


@dataclass
class FakeHandler:
    fail_times: int = 0
    calls: int = 0

    async def handle(self, event: EventEnvelope) -> None:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("handler boom")


@dataclass
class FakeDlq:
    calls: int = 0
    fail: bool = False

    async def publish_failed(
        self,
        consumed_event: ConsumedEvent,
        error: EventProcessingError,
        attempts: int,
    ) -> None:
        self.calls += 1
        if self.fail:
            raise DlqUnavailableError("dlq down")


async def _async_noop(_delay: float = 0.0) -> None:
    return None


def test_retry_policy_bounded_and_deterministic() -> None:
    policy = RetryPolicy(
        max_attempts=4,
        initial_delay_seconds=0.1,
        max_delay_seconds=1.0,
        multiplier=2.0,
    )
    assert policy.delays() == [0.1, 0.2, 0.4]


@pytest.mark.asyncio
async def test_worker_commits_on_success() -> None:
    event = _consumed()
    consumer = FakeConsumer()
    worker = ConsumerWorker(
        consumer=consumer,
        handler=FakeHandler(),
        retry_policy=RetryPolicy(max_attempts=2, initial_delay_seconds=0),
        sleeper=_async_noop,
    )
    await worker._process(event)  # noqa: SLF001
    assert len(consumer.commits) == 1
    assert consumer.commits[0].offset == event.offset


@pytest.mark.asyncio
async def test_worker_does_not_commit_on_handler_failure() -> None:
    event = _consumed()
    consumer = FakeConsumer()
    worker = ConsumerWorker(
        consumer=consumer,
        handler=FakeHandler(fail_times=99),
        retry_policy=RetryPolicy(max_attempts=2, initial_delay_seconds=0),
        sleeper=_async_noop,
    )
    with pytest.raises(EventRetryExhaustedError):
        await worker._process(event)  # noqa: SLF001
    assert consumer.commits == []


@pytest.mark.asyncio
async def test_worker_retries_expected_times() -> None:
    event = _consumed()
    consumer = FakeConsumer()
    handler = FakeHandler(fail_times=2)
    worker = ConsumerWorker(
        consumer=consumer,
        handler=handler,
        retry_policy=RetryPolicy(max_attempts=3, initial_delay_seconds=0),
        sleeper=_async_noop,
    )
    await worker._process(event)  # noqa: SLF001
    assert handler.calls == 3
    assert len(consumer.commits) == 1


@pytest.mark.asyncio
async def test_worker_calls_dlq_then_fail_closed() -> None:
    event = _consumed()
    consumer = FakeConsumer()
    dlq = FakeDlq()
    worker = ConsumerWorker(
        consumer=consumer,
        handler=FakeHandler(fail_times=99),
        retry_policy=RetryPolicy(max_attempts=2, initial_delay_seconds=0),
        dlq=dlq,
        sleeper=_async_noop,
    )
    with pytest.raises(EventRetryExhaustedError):
        await worker._process(event)  # noqa: SLF001
    assert dlq.calls == 1
    assert consumer.commits == []


@pytest.mark.asyncio
async def test_worker_fail_closed_when_dlq_missing() -> None:
    event = _consumed()
    consumer = FakeConsumer()
    worker = ConsumerWorker(
        consumer=consumer,
        handler=FakeHandler(fail_times=99),
        retry_policy=RetryPolicy(max_attempts=1, initial_delay_seconds=0),
        dlq=None,
        sleeper=_async_noop,
    )
    with pytest.raises(EventRetryExhaustedError, match="no DLQ"):
        await worker._process(event)  # noqa: SLF001
    assert consumer.commits == []


@pytest.mark.asyncio
async def test_worker_cancellation_exits_cleanly() -> None:
    consumer = FakeConsumer()
    worker = ConsumerWorker(
        consumer=consumer,
        handler=FakeHandler(),
        retry_policy=RetryPolicy(max_attempts=1),
        sleeper=_async_noop,
    )
    task = worker.start()
    await worker.stop()
    assert task.cancelled() or task.done()
