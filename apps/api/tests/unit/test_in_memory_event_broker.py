"""Unit tests for InMemoryEventBroker determinism."""

from __future__ import annotations

import pytest
from tests.support.kafka.broker import InMemoryEventBroker


def test_explicit_topic_creation() -> None:
    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=2)
    assert broker.has_topic("events")
    assert broker.partition_count("events") == 2


def test_unknown_topic_publish_fails() -> None:
    broker = InMemoryEventBroker()
    with pytest.raises(ValueError, match="unknown topic"):
        broker.publish("events", value=b"{}")


def test_offset_increments() -> None:
    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=1)
    r0 = broker.publish("events", value=b"a")
    r1 = broker.publish("events", value=b"b")
    assert r0.offset == 0
    assert r1.offset == 1


def test_stable_key_partitioning() -> None:
    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=4)
    key = b"same-key"
    partitions = {broker.publish("events", value=b"1", key=key).partition for _ in range(5)}
    assert len(partitions) == 1


def test_deterministic_round_robin() -> None:
    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=3)
    partitions = [broker.publish("events", value=bytes([i])).partition for i in range(6)]
    assert partitions == [0, 1, 2, 0, 1, 2]


def test_broker_reset_clears_state() -> None:
    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=1)
    broker.publish("events", value=b"x")
    broker.commit(group_id="g", topic="events", partition=0, next_offset=1)
    broker.reset()
    assert not broker.has_topic("events")
    assert broker.committed_offset(group_id="g", topic="events", partition=0) == 0


def test_no_shared_global_state() -> None:
    a = InMemoryEventBroker()
    b = InMemoryEventBroker()
    a.create_topic("events", partitions=1)
    assert not b.has_topic("events")


def test_serialized_bytes_immutable_after_publish() -> None:
    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=1)
    buf = bytearray(b'{"a":1}')
    record = broker.publish("events", value=buf)
    buf[:] = b"XXXXXXX"
    assert record.value == b'{"a":1}'
    assert broker.records("events", 0)[0].value == b'{"a":1}'


def test_duplicate_topic_creation_fails() -> None:
    broker = InMemoryEventBroker()
    broker.create_topic("events", partitions=1)
    with pytest.raises(ValueError, match="already exists"):
        broker.create_topic("events", partitions=1)
