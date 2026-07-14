"""Bounded Iceberg write micro-batch (#307)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.events.ports import ConsumedEvent
from app.infrastructure.iceberg.errors import IcebergBatchError, IcebergDuplicateBatchKeyError


@dataclass(slots=True)
class BatchItem:
    consumed: ConsumedEvent
    table_name: str
    row: dict[str, Any]
    idempotency_key: str
    approx_bytes: int


@dataclass
class WriteBatch:
    """In-memory bounded batch. Ordered by append (= Kafka consume) order."""

    max_records: int
    max_bytes: int
    items: list[BatchItem] = field(default_factory=list)
    _keys: set[str] = field(default_factory=set)
    _bytes: int = 0

    def __len__(self) -> int:
        return len(self.items)

    @property
    def total_bytes(self) -> int:
        return self._bytes

    def is_empty(self) -> bool:
        return not self.items

    def would_overflow(self, *, approx_bytes: int) -> bool:
        if approx_bytes > self.max_bytes:
            return True
        if not self.items:
            return False
        return len(self.items) + 1 > self.max_records or self._bytes + approx_bytes > self.max_bytes

    def add(self, item: BatchItem) -> None:
        if item.approx_bytes > self.max_bytes:
            msg = "record exceeds batch_max_bytes"
            raise IcebergBatchError(msg)
        if item.idempotency_key in self._keys:
            msg = "duplicate idempotency_key in uncommitted batch"
            raise IcebergDuplicateBatchKeyError(msg)
        would_overflow = len(self.items) + 1 > self.max_records or (
            self._bytes + item.approx_bytes > self.max_bytes
        )
        if self.items and would_overflow:
            msg = "batch capacity exceeded"
            raise IcebergBatchError(msg)
        self.items.append(item)
        self._keys.add(item.idempotency_key)
        self._bytes += item.approx_bytes

    def clear(self) -> None:
        self.items.clear()
        self._keys.clear()
        self._bytes = 0

    def sorted_for_flush(self) -> list[BatchItem]:
        """Deterministic flush order: (topic, partition, offset)."""
        return sorted(
            self.items,
            key=lambda i: (i.consumed.topic, i.consumed.partition, i.consumed.offset),
        )
