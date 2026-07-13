"""Worker runtime integration over the in-memory harness."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.events.envelope import EventEnvelope
from app.events.errors import EventRetryExhaustedError
from app.events.topics import KafkaTopic
from tests.support.kafka.fixtures import event_runtime_harness


async def _wait_until(predicate, *, timeout: float = 1.0) -> None:
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        if predicate():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("condition not met before timeout")


def _event() -> EventEnvelope:
    return EventEnvelope(
        event_id=uuid4(),
        event_type="test.event",
        schema_version="1",
        source_system="test",
        occurred_at=datetime(2026, 7, 12, tzinfo=UTC),
        ingested_at=datetime(2026, 7, 12, tzinfo=UTC),
        idempotency_key="worker-1",
        payload={"ok": True},
    )


@pytest.mark.asyncio
async def test_worker_processes_and_commits() -> None:
    async with event_runtime_harness() as harness:
        await harness.producer.publish(KafkaTopic.EVENTS, _event())
        await _wait_until(lambda: harness.handler.calls == 1)
        assert (
            harness.broker.committed_offset(group_id="test-group", topic="events", partition=0) == 1
        )


@pytest.mark.asyncio
async def test_worker_failure_does_not_commit() -> None:
    async with event_runtime_harness(fail_times=99, max_attempts=1) as harness:
        await harness.producer.publish(KafkaTopic.EVENTS, _event())
        task = harness.worker.task
        assert task is not None
        with pytest.raises(EventRetryExhaustedError):
            await task
        assert (
            harness.broker.committed_offset(group_id="test-group", topic="events", partition=0) == 0
        )


@pytest.mark.asyncio
async def test_multi_topic_worker_isolation() -> None:
    async with event_runtime_harness(topics=["events", "audit"]) as events_harness:
        await events_harness.producer.publish(KafkaTopic.EVENTS, _event())
        await _wait_until(lambda: events_harness.handler.calls == 1)
        assert all(e.event_type == "test.event" for e in events_harness.handler.events)


@pytest.mark.asyncio
async def test_worker_shutdown_idempotent_and_no_leaked_tasks() -> None:
    async with event_runtime_harness() as harness:
        await harness.stop()
        await harness.stop()
        assert harness.worker.task is None
