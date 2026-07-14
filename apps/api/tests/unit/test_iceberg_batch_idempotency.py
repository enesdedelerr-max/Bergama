"""Batch bounds and process-local committed-key index tests (#307)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.core.clock import FixedClock
from app.events.envelope import EventEnvelope
from app.events.ports import ConsumedEvent
from app.infrastructure.iceberg.batch import BatchItem, WriteBatch
from app.infrastructure.iceberg.errors import IcebergBatchError, IcebergDuplicateBatchKeyError
from app.infrastructure.iceberg.idempotency import CommittedKeyIndex


def _item(key: str, *, offset: int = 0, approx_bytes: int = 10) -> BatchItem:
    envelope = EventEnvelope(
        event_id=uuid4(),
        event_type="market.quote",
        schema_version="1.0.0",
        source_system="bergama-market-data",
        occurred_at=datetime(2026, 7, 13, 14, 30, tzinfo=UTC),
        ingested_at=datetime(2026, 7, 13, 14, 30, tzinfo=UTC),
        idempotency_key=key,
        payload={},
    )
    consumed = ConsumedEvent(
        envelope=envelope,
        topic="market-data",
        partition=0,
        offset=offset,
        timestamp=None,
        key=key,
        headers={},
    )
    return BatchItem(
        consumed=consumed,
        table_name="market_quotes",
        row={"idempotency_key": key},
        idempotency_key=key,
        approx_bytes=approx_bytes,
    )


def test_batch_record_and_byte_bounds() -> None:
    batch = WriteBatch(max_records=2, max_bytes=50)
    batch.add(_item("a", offset=0, approx_bytes=20))
    batch.add(_item("b", offset=1, approx_bytes=20))
    assert batch.would_overflow(approx_bytes=10)
    with pytest.raises(IcebergBatchError):
        batch.add(_item("c", offset=2, approx_bytes=10))


def test_oversized_record_fails_closed() -> None:
    batch = WriteBatch(max_records=10, max_bytes=50)
    with pytest.raises(IcebergBatchError, match="batch_max_bytes"):
        batch.add(_item("big", approx_bytes=51))


def test_same_batch_duplicate_fails_before_write() -> None:
    batch = WriteBatch(max_records=10, max_bytes=10_000)
    batch.add(_item("dup", offset=0))
    with pytest.raises(IcebergDuplicateBatchKeyError):
        batch.add(_item("dup", offset=1))


def test_flush_order_by_topic_partition_offset() -> None:
    batch = WriteBatch(max_records=10, max_bytes=10_000)
    batch.add(_item("c", offset=2))
    batch.add(_item("a", offset=0))
    batch.add(_item("b", offset=1))
    ordered = batch.sorted_for_flush()
    assert [i.consumed.offset for i in ordered] == [0, 1, 2]


def test_committed_key_index_ttl_and_bound() -> None:
    clock = FixedClock(datetime(2026, 7, 13, 12, 0, tzinfo=UTC))
    index = CommittedKeyIndex(clock=clock, ttl_seconds=60, max_entries=2)
    index.add_many(["k1", "k2"])
    assert index.contains("k1")
    assert len(index) == 2
    index.add_many(["k3"])
    assert not index.contains("k1")
    assert index.contains("k2")
    assert index.contains("k3")
    clock._instant = clock.now() + timedelta(seconds=61)
    assert not index.contains("k2")
    assert not index.contains("k3")
