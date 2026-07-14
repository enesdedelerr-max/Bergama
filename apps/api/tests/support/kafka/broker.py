"""Test-only in-memory event broker. Never used by production wiring."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock


@dataclass(frozen=True, slots=True)
class BrokerRecord:
    """Immutable published record snapshot (serialized value bytes)."""

    topic: str
    partition: int
    offset: int
    timestamp: datetime
    key: bytes | None
    value: bytes
    headers: tuple[tuple[str, str], ...]


@dataclass
class _TopicState:
    partition_count: int
    records: dict[int, list[BrokerRecord]] = field(default_factory=dict)
    next_offsets: dict[int, int] = field(default_factory=dict)
    round_robin: int = 0

    def __post_init__(self) -> None:
        for partition in range(self.partition_count):
            self.records.setdefault(partition, [])
            self.next_offsets.setdefault(partition, 0)


class InMemoryEventBroker:
    """Deterministic broker for tests. Explicit topic creation. No auto-commit."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._topics: dict[str, _TopicState] = {}
        # group_id -> topic -> partition -> next_offset
        self._commits: dict[str, dict[str, dict[int, int]]] = {}

    def reset(self) -> None:
        with self._lock:
            self._topics.clear()
            self._commits.clear()

    def create_topic(self, topic: str, *, partitions: int = 1) -> None:
        if partitions < 1:
            msg = "partitions must be >= 1"
            raise ValueError(msg)
        with self._lock:
            if topic in self._topics:
                msg = f"topic already exists: {topic}"
                raise ValueError(msg)
            self._topics[topic] = _TopicState(partition_count=partitions)

    def has_topic(self, topic: str) -> bool:
        with self._lock:
            return topic in self._topics

    def partition_count(self, topic: str) -> int:
        with self._lock:
            state = self._topics.get(topic)
            if state is None:
                msg = f"unknown topic: {topic}"
                raise ValueError(msg)
            return state.partition_count

    def publish(
        self,
        topic: str,
        *,
        value: bytes,
        key: bytes | None = None,
        headers: dict[str, str] | None = None,
        timestamp: datetime | None = None,
    ) -> BrokerRecord:
        # Copy bytes so later mutation of caller buffers cannot affect broker state.
        value_snapshot = bytes(value)
        key_snapshot = None if key is None else bytes(key)
        header_items = tuple(sorted((headers or {}).items()))
        ts = timestamp or datetime.now(UTC)
        with self._lock:
            state = self._topics.get(topic)
            if state is None:
                msg = f"unknown topic: {topic}"
                raise ValueError(msg)
            partition = _select_partition(state, key_snapshot)
            offset = state.next_offsets[partition]
            record = BrokerRecord(
                topic=topic,
                partition=partition,
                offset=offset,
                timestamp=ts,
                key=key_snapshot,
                value=value_snapshot,
                headers=header_items,
            )
            state.records[partition].append(record)
            state.next_offsets[partition] = offset + 1
            return record

    def read(
        self,
        *,
        group_id: str,
        topic: str,
        partition: int,
    ) -> BrokerRecord | None:
        with self._lock:
            state = self._topics.get(topic)
            if state is None:
                msg = f"unknown topic: {topic}"
                raise ValueError(msg)
            if partition < 0 or partition >= state.partition_count:
                msg = f"invalid partition {partition} for topic {topic}"
                raise ValueError(msg)
            next_offset = self._commits.get(group_id, {}).get(topic, {}).get(partition, 0)
            records = state.records[partition]
            if next_offset >= len(records):
                return None
            return records[next_offset]

    def commit(self, *, group_id: str, topic: str, partition: int, next_offset: int) -> None:
        with self._lock:
            if topic not in self._topics:
                msg = f"unknown topic: {topic}"
                raise ValueError(msg)
            group = self._commits.setdefault(group_id, {})
            topic_commits = group.setdefault(topic, {})
            topic_commits[partition] = next_offset

    def committed_offset(self, *, group_id: str, topic: str, partition: int) -> int:
        with self._lock:
            return self._commits.get(group_id, {}).get(topic, {}).get(partition, 0)

    def records(self, topic: str, partition: int) -> list[BrokerRecord]:
        with self._lock:
            state = self._topics[topic]
            return list(state.records[partition])


def _select_partition(state: _TopicState, key: bytes | None) -> int:
    if key is None:
        partition = state.round_robin % state.partition_count
        state.round_robin += 1
        return partition
    digest = hashlib.sha256(key).digest()
    return int.from_bytes(digest[:8], "big") % state.partition_count
