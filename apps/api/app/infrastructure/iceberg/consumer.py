"""Dedicated IcebergWriterWorker — batch consume/flush/offset commit (#307).

Ordering: preserve Kafka consume order within each partition; flush sorted by
(topic, partition, offset). Cross-partition order is undefined.

Semantics:
- at-least-once Kafka delivery
- append-only Iceberg storage
- process-local committed-key replay suppression only
- no exactly-once guarantee
- multi-table snapshots are not one atomic transaction
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any

from app.core.clock import Clock, SystemClock
from app.core.iceberg_writer_settings import IcebergWriterSettings
from app.core.logging import get_logger, structured_extra
from app.events.errors import EventDeserializationError
from app.events.ports import ConsumedEvent, EventConsumer
from app.infrastructure.iceberg.batch import BatchItem, WriteBatch
from app.infrastructure.iceberg.errors import (
    IcebergBatchError,
    IcebergDuplicateBatchKeyError,
    IcebergOffsetCommitError,
    IcebergShutdownFlushError,
    IcebergWriterError,
)
from app.infrastructure.iceberg.idempotency import CommittedKeyIndex
from app.infrastructure.iceberg.mapper import (
    estimate_row_bytes,
    map_envelope_to_row,
    reconstruct_canonical_event,
)
from app.infrastructure.iceberg.routing import table_for_event_type
from app.infrastructure.iceberg.writer import IcebergTableWriter

logger = get_logger(__name__)


class IcebergWriterWorker:
    """Owns a dedicated EventConsumer and bounded append-only Iceberg flush loop."""

    def __init__(
        self,
        *,
        consumer: EventConsumer,
        table_writer: IcebergTableWriter,
        settings: IcebergWriterSettings,
        committed_keys: CommittedKeyIndex,
        clock: Clock | None = None,
        name: str = "iceberg-writer",
    ) -> None:
        self._consumer = consumer
        self._writer = table_writer
        self._settings = settings
        self._keys = committed_keys
        self._clock = clock or SystemClock()
        self._name = name
        self._batch = WriteBatch(
            max_records=settings.batch_max_records,
            max_bytes=settings.batch_max_bytes,
        )
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()
        self._intake_stopped = False
        self._last_flush_at = self._clock.now()
        self._started = False
        self._closed = False

    @property
    def started(self) -> bool:
        return self._started

    @property
    def batch_size(self) -> int:
        return len(self._batch)

    async def start(self) -> None:
        if self._closed:
            msg = "IcebergWriterWorker is closed"
            raise IcebergWriterError(msg)
        if self._started:
            return
        await self._consumer.start()
        self._stop.clear()
        self._intake_stopped = False
        self._last_flush_at = self._clock.now()
        self._task = asyncio.create_task(self._run(), name=f"iceberg-worker:{self._name}")
        self._started = True
        logger.info(
            "iceberg writer worker started",
            extra=structured_extra(
                event="iceberg_writer.started",
                source="iceberg.worker",
                worker=self._name,
            ),
        )

    async def stop(self) -> None:
        """Stop intake, flush pending batch, then stop consumer."""
        self._intake_stopped = True
        self._stop.set()
        task = self._task
        if task is not None and not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self._task = None
        try:
            await self._flush(reason="shutdown")
        except Exception as exc:
            msg = "shutdown flush failed"
            raise IcebergShutdownFlushError(msg) from exc
        finally:
            await self._consumer.stop()
            self._started = False
            logger.info(
                "iceberg writer worker stopped",
                extra=structured_extra(
                    event="iceberg_writer.stopped",
                    source="iceberg.worker",
                    worker=self._name,
                ),
            )

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._started:
            await self.stop()

    async def _run(self) -> None:
        try:
            while not self._stop.is_set() and not self._intake_stopped:
                try:
                    consumed = await asyncio.wait_for(self._consumer.get(), timeout=0.25)
                except TimeoutError:
                    await self._flush_if_due()
                    continue
                except asyncio.CancelledError:
                    raise
                except EventDeserializationError:
                    # Offset must not advance — stop the worker fail-closed.
                    logger.error(
                        "iceberg writer envelope deserialization failed",
                        exc_info=True,
                        extra=structured_extra(
                            event="iceberg_writer.deserialize_failed",
                            source="iceberg.worker",
                        ),
                    )
                    raise
                await self._accept(consumed)
                await self._flush_if_needed()
        except asyncio.CancelledError:
            return

    async def _accept(self, consumed: ConsumedEvent) -> None:
        envelope = consumed.envelope
        event = reconstruct_canonical_event(envelope)
        table = table_for_event_type(envelope.event_type, table_prefix=self._settings.table_prefix)
        row = map_envelope_to_row(envelope, event)
        key = row["idempotency_key"]
        if self._keys.contains(key):
            # Process-local suppression — still commit Kafka offset for this record alone.
            await self._commit_single(consumed)
            logger.info(
                "iceberg writer suppressed process-local duplicate",
                extra=structured_extra(
                    event="iceberg_writer.local_duplicate_suppressed",
                    source="iceberg.worker",
                    # Do not log full key if extreme; key is non-secret market identity.
                ),
            )
            return
        approx = estimate_row_bytes(row)
        item = BatchItem(
            consumed=consumed,
            table_name=table,
            row=row,
            idempotency_key=key,
            approx_bytes=approx,
        )
        if self._batch.would_overflow(approx_bytes=approx) and not self._batch.is_empty():
            await self._flush(reason="capacity")
        try:
            self._batch.add(item)
        except IcebergDuplicateBatchKeyError:
            raise
        except IcebergBatchError:
            # Oversized single record
            raise

    async def _flush_if_needed(self) -> None:
        if len(self._batch) >= self._settings.batch_max_records:
            await self._flush(reason="max_records")
            return
        if self._batch.total_bytes >= self._settings.batch_max_bytes:
            await self._flush(reason="max_bytes")

    async def _flush_if_due(self) -> None:
        if self._batch.is_empty():
            return
        elapsed = (self._clock.now() - self._last_flush_at).total_seconds()
        if elapsed >= self._settings.flush_interval_seconds:
            await self._flush(reason="interval")

    async def _flush(self, *, reason: str) -> None:
        if self._batch.is_empty():
            self._last_flush_at = self._clock.now()
            return
        items = self._batch.sorted_for_flush()
        # Snapshot appends — any failure leaves offsets uncommitted and index untouched.
        self._writer.append_batch(items)
        try:
            await self._commit_offsets(items)
        except Exception as exc:
            msg = "Kafka offset commit failed after Iceberg snapshots"
            raise IcebergOffsetCommitError(msg) from exc
        self._keys.add_many([item.idempotency_key for item in items])
        self._batch.clear()
        self._last_flush_at = self._clock.now()
        logger.info(
            "iceberg writer batch flushed",
            extra=structured_extra(
                event="iceberg_writer.flushed",
                source="iceberg.worker",
                reason=reason,
                record_count=len(items),
            ),
        )

    async def _commit_offsets(self, items: list[BatchItem]) -> None:
        """Commit the highest offset per (topic, partition) in deterministic order."""
        highest: dict[tuple[str, int], ConsumedEvent] = {}
        for item in items:
            key = (item.consumed.topic, item.consumed.partition)
            current = highest.get(key)
            if current is None or item.consumed.offset > current.offset:
                highest[key] = item.consumed
        for key in sorted(highest):
            await self._consumer.commit(highest[key])

    async def _commit_single(self, consumed: ConsumedEvent) -> None:
        await self._consumer.commit(consumed)


class IcebergWriterRuntime:
    """Application-scoped Iceberg writer lifecycle owner."""

    def __init__(
        self,
        *,
        worker: IcebergWriterWorker,
        catalog: Any,
        settings: IcebergWriterSettings,
    ) -> None:
        self.worker = worker
        self.catalog = catalog
        self.settings = settings
        self._started = False
        self._closed = False

    @property
    def started(self) -> bool:
        return self._started

    async def start(self) -> None:
        if self._closed or self._started:
            return
        await self.worker.start()
        self._started = True

    async def stop(self) -> None:
        if not self._started:
            return
        await self.worker.stop()
        self._started = False

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            if self._started:
                await self.stop()
        finally:
            # Catalog/FileIO cleanup — SqlCatalog has no close; REST may hold clients.
            close = getattr(self.catalog, "close", None)
            if callable(close):
                result = close()
                if asyncio.iscoroutine(result):
                    await result
