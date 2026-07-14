"""Offline Iceberg writer integration tests (#307).

Uses FakeEventConsumer + SqlCatalog/file warehouse.
No live Kafka/MinIO required.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.core.clock import FixedClock
from app.core.environment import AppEnvironment
from app.core.iceberg_writer_settings import IcebergWriterSettings
from app.events.topics import KafkaTopic, TopicRegistry
from app.infrastructure.iceberg.catalog import (
    build_catalog,
    build_offline_sql_settings,
    ensure_market_tables,
    load_required_table,
)
from app.infrastructure.iceberg.consumer import IcebergWriterWorker
from app.infrastructure.iceberg.errors import IcebergShutdownFlushError, IcebergSnapshotError
from app.infrastructure.iceberg.idempotency import CommittedKeyIndex
from app.infrastructure.iceberg.writer import IcebergTableWriter
from app.market_data.keys import build_idempotency_key
from app.market_data.serialization import market_event_to_envelope
from tests.support.kafka.broker import InMemoryEventBroker
from tests.support.kafka.consumer import FakeEventConsumer
from tests.support.kafka.producer import FakeEventProducer
from tests.support.market_data_fixtures import make_bar, make_quote, make_trade


async def _wait_until(predicate: object, *, timeout: float = 2.0) -> None:
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        if predicate():  # type: ignore[operator]
            return
        await asyncio.sleep(0.01)
    msg = "condition not met before timeout"
    raise AssertionError(msg)


@pytest.fixture
def warehouse(tmp_path: Path) -> Path:
    return tmp_path / "warehouse"


@pytest.fixture
def writer_settings(warehouse: Path) -> IcebergWriterSettings:
    return build_offline_sql_settings(warehouse)


@pytest.fixture
def catalog(writer_settings: IcebergWriterSettings):
    catalog = build_catalog(writer_settings)
    ensure_market_tables(catalog, writer_settings, environment=AppEnvironment.TEST)
    return catalog


@pytest.mark.asyncio
async def test_consume_append_snapshot_then_offset(
    warehouse: Path,
    writer_settings: IcebergWriterSettings,
    catalog: object,
) -> None:
    registry = TopicRegistry()
    broker = InMemoryEventBroker()
    topic = registry.resolve(KafkaTopic.MARKET_DATA)
    broker.create_topic(topic)
    event = make_quote()
    envelope = market_event_to_envelope(event)
    producer = FakeEventProducer(broker, registry, clock=datetime(2026, 7, 13, 14, 30, tzinfo=UTC))
    await producer.start()
    await producer.publish(KafkaTopic.MARKET_DATA, envelope, key=build_idempotency_key(event))

    consumer = FakeEventConsumer(
        broker,
        group_id=writer_settings.consumer_group_id,
        topics=[KafkaTopic.MARKET_DATA.value],
        topic_registry=registry,
        poll_interval_seconds=0.005,
    )
    clock = FixedClock(datetime(2026, 7, 13, 15, 0, tzinfo=UTC))
    settings = writer_settings.model_copy(
        update={"batch_max_records": 1, "flush_interval_seconds": 60.0}
    )
    worker = IcebergWriterWorker(
        consumer=consumer,
        table_writer=IcebergTableWriter(catalog, settings),  # type: ignore[arg-type]
        settings=settings,
        committed_keys=CommittedKeyIndex(clock=clock, ttl_seconds=3600, max_entries=1000),
        clock=clock,
    )
    await worker.start()
    try:
        await _wait_until(
            lambda: (
                broker.committed_offset(
                    group_id=writer_settings.consumer_group_id, topic=topic, partition=0
                )
                == 1
            )
        )
        table = load_required_table(catalog, namespace="bergama", table_name="market_quotes")  # type: ignore[arg-type]
        rows = table.scan().to_arrow()
        assert len(rows) == 1
        assert rows["idempotency_key"][0].as_py() == build_idempotency_key(event)
        assert rows["event_id"][0].as_py() == str(envelope.event_id)
        assert worker._keys.contains(build_idempotency_key(event))
    finally:
        await worker.aclose()


@pytest.mark.asyncio
async def test_multi_table_partial_failure_no_offset_no_index(
    warehouse: Path,
    writer_settings: IcebergWriterSettings,
    catalog: object,
) -> None:
    registry = TopicRegistry()
    broker = InMemoryEventBroker()
    topic = registry.resolve(KafkaTopic.MARKET_DATA)
    broker.create_topic(topic)
    quote = make_quote(source=make_quote().source.model_copy(update={"source_event_id": "q1"}))
    trade = make_trade(source=make_trade().source.model_copy(update={"source_event_id": "t1"}))
    producer = FakeEventProducer(broker, registry, clock=datetime(2026, 7, 13, 14, 30, tzinfo=UTC))
    await producer.start()
    await producer.publish(
        KafkaTopic.MARKET_DATA, market_event_to_envelope(quote), key=build_idempotency_key(quote)
    )
    await producer.publish(
        KafkaTopic.MARKET_DATA, market_event_to_envelope(trade), key=build_idempotency_key(trade)
    )

    class BoomWriter(IcebergTableWriter):
        def append_batch(self, items):  # type: ignore[no-untyped-def]
            # Commit quotes successfully, then fail trades to model partial multi-table failure.
            quotes = [i for i in items if i.table_name == "market_quotes"]
            trades = [i for i in items if i.table_name == "market_trades"]
            if quotes:
                super().append_batch(quotes)
            if trades:
                raise IcebergSnapshotError("simulated trade snapshot failure")
            return []

    consumer = FakeEventConsumer(
        broker,
        group_id=writer_settings.consumer_group_id,
        topics=[KafkaTopic.MARKET_DATA.value],
        topic_registry=registry,
    )
    clock = FixedClock(datetime(2026, 7, 13, 15, 0, tzinfo=UTC))
    settings = writer_settings.model_copy(
        update={"batch_max_records": 2, "flush_interval_seconds": 60.0}
    )
    keys = CommittedKeyIndex(clock=clock, ttl_seconds=3600, max_entries=1000)
    worker = IcebergWriterWorker(
        consumer=consumer,
        table_writer=BoomWriter(catalog, settings),  # type: ignore[arg-type]
        settings=settings,
        committed_keys=keys,
        clock=clock,
    )
    await worker.start()
    try:
        await asyncio.sleep(0.2)
        assert (
            broker.committed_offset(
                group_id=writer_settings.consumer_group_id, topic=topic, partition=0
            )
            == 0
        )
        assert not keys.contains(build_idempotency_key(quote))
        assert not keys.contains(build_idempotency_key(trade))
    finally:
        with pytest.raises((IcebergSnapshotError, IcebergShutdownFlushError)):
            await worker.aclose()


@pytest.mark.asyncio
async def test_process_local_duplicate_suppressed_after_success(
    warehouse: Path,
    writer_settings: IcebergWriterSettings,
    catalog: object,
) -> None:
    registry = TopicRegistry()
    broker = InMemoryEventBroker()
    topic = registry.resolve(KafkaTopic.MARKET_DATA)
    broker.create_topic(topic)
    event = make_bar()
    envelope = market_event_to_envelope(event)
    key = build_idempotency_key(event)
    producer = FakeEventProducer(broker, registry, clock=datetime(2026, 7, 13, 14, 30, tzinfo=UTC))
    await producer.start()
    await producer.publish(KafkaTopic.MARKET_DATA, envelope, key=key)

    consumer = FakeEventConsumer(
        broker,
        group_id=writer_settings.consumer_group_id,
        topics=[KafkaTopic.MARKET_DATA.value],
        topic_registry=registry,
    )
    clock = FixedClock(datetime(2026, 7, 13, 15, 0, tzinfo=UTC))
    settings = writer_settings.model_copy(update={"batch_max_records": 1})
    keys = CommittedKeyIndex(clock=clock, ttl_seconds=3600, max_entries=1000)
    worker = IcebergWriterWorker(
        consumer=consumer,
        table_writer=IcebergTableWriter(catalog, settings),  # type: ignore[arg-type]
        settings=settings,
        committed_keys=keys,
        clock=clock,
    )
    await worker.start()
    try:
        await _wait_until(
            lambda: (
                broker.committed_offset(
                    group_id=writer_settings.consumer_group_id, topic=topic, partition=0
                )
                == 1
            )
        )
        # Re-publish same logical key (new envelope event_id) — process-local suppress.
        replay = market_event_to_envelope(event)
        await producer.publish(KafkaTopic.MARKET_DATA, replay, key=key)
        await _wait_until(
            lambda: (
                broker.committed_offset(
                    group_id=writer_settings.consumer_group_id, topic=topic, partition=0
                )
                == 2
            )
        )
        table = load_required_table(catalog, namespace="bergama", table_name="market_bars")  # type: ignore[arg-type]
        assert len(table.scan().to_arrow()) == 1
    finally:
        await worker.aclose()


@pytest.mark.asyncio
async def test_restart_allows_visible_duplicate(
    warehouse: Path,
    writer_settings: IcebergWriterSettings,
    catalog: object,
) -> None:
    """Fresh process-local index (restart) may append a visible duplicate under append-only MVP."""
    registry = TopicRegistry()
    source = make_quote().source.model_copy(update={"source_event_id": "restart-1"})
    event = make_quote(source=source)
    key = build_idempotency_key(event)

    for label in ("r1", "r2"):
        broker = InMemoryEventBroker()
        topic = registry.resolve(KafkaTopic.MARKET_DATA)
        broker.create_topic(topic)
        producer = FakeEventProducer(
            broker, registry, clock=datetime(2026, 7, 13, 14, 30, tzinfo=UTC)
        )
        await producer.start()
        await producer.publish(KafkaTopic.MARKET_DATA, market_event_to_envelope(event), key=key)
        consumer = FakeEventConsumer(
            broker,
            group_id=f"g-{label}",
            topics=[KafkaTopic.MARKET_DATA.value],
            topic_registry=registry,
        )
        clock = FixedClock(datetime(2026, 7, 13, 15, 0, tzinfo=UTC))
        settings = writer_settings.model_copy(update={"batch_max_records": 1})
        worker = IcebergWriterWorker(
            consumer=consumer,
            table_writer=IcebergTableWriter(catalog, settings),  # type: ignore[arg-type]
            settings=settings,
            # New index each iteration simulates process restart.
            committed_keys=CommittedKeyIndex(clock=clock, ttl_seconds=3600, max_entries=1000),
            clock=clock,
        )
        await worker.start()
        try:
            await _wait_until(
                lambda g=label, t=topic, b=broker: (
                    b.committed_offset(group_id=f"g-{g}", topic=t, partition=0) == 1
                )
            )
        finally:
            await worker.aclose()

    table = load_required_table(catalog, namespace="bergama", table_name="market_quotes")  # type: ignore[arg-type]
    assert len(table.scan().to_arrow()) == 2


@pytest.mark.asyncio
async def test_same_batch_duplicate_fails_closed(
    warehouse: Path,
    writer_settings: IcebergWriterSettings,
    catalog: object,
) -> None:
    registry = TopicRegistry()
    broker = InMemoryEventBroker()
    topic = registry.resolve(KafkaTopic.MARKET_DATA)
    broker.create_topic(topic)
    event = make_trade()
    key = build_idempotency_key(event)
    producer = FakeEventProducer(broker, registry, clock=datetime(2026, 7, 13, 14, 30, tzinfo=UTC))
    await producer.start()
    await producer.publish(KafkaTopic.MARKET_DATA, market_event_to_envelope(event), key=key)
    await producer.publish(KafkaTopic.MARKET_DATA, market_event_to_envelope(event), key=key)

    consumer = FakeEventConsumer(
        broker,
        group_id=writer_settings.consumer_group_id,
        topics=[KafkaTopic.MARKET_DATA.value],
        topic_registry=registry,
    )
    clock = FixedClock(datetime(2026, 7, 13, 15, 0, tzinfo=UTC))
    settings = writer_settings.model_copy(
        update={"batch_max_records": 10, "flush_interval_seconds": 30.0}
    )
    worker = IcebergWriterWorker(
        consumer=consumer,
        table_writer=IcebergTableWriter(catalog, settings),  # type: ignore[arg-type]
        settings=settings,
        committed_keys=CommittedKeyIndex(clock=clock, ttl_seconds=3600, max_entries=1000),
        clock=clock,
    )
    await worker.start()
    try:
        await asyncio.sleep(0.15)
        # Worker should fail on second accept; offset stays 0; no rows.
        assert (
            broker.committed_offset(
                group_id=writer_settings.consumer_group_id, topic=topic, partition=0
            )
            == 0
        )
        table = load_required_table(catalog, namespace="bergama", table_name="market_trades")  # type: ignore[arg-type]
        assert len(table.scan().to_arrow()) == 0
    finally:
        await worker.aclose()
