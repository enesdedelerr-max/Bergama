"""Consumer worker: deserialize already done by consumer; handle, retry, commit."""

from __future__ import annotations

import asyncio
import contextlib

from app.core.logging import get_logger, structured_extra
from app.events.errors import (
    DlqUnavailableError,
    EventProcessingError,
    EventRetryExhaustedError,
)
from app.events.ports import ConsumedEvent, DlqPublisher, EventConsumer, EventHandler
from app.events.retry import AsyncSleeper, RetryPolicy

logger = get_logger(__name__)


class ConsumerWorker:
    """Process consumed events with manual commit and fail-closed exhaustion."""

    def __init__(
        self,
        *,
        consumer: EventConsumer,
        handler: EventHandler,
        retry_policy: RetryPolicy,
        dlq: DlqPublisher | None = None,
        sleeper: AsyncSleeper | None = None,
        name: str = "default",
    ) -> None:
        self._consumer = consumer
        self._handler = handler
        self._retry = retry_policy
        self._dlq = dlq
        self._sleeper: AsyncSleeper = sleeper or asyncio.sleep
        self._name = name
        self._task: asyncio.Task[None] | None = None
        self._stopped = asyncio.Event()

    @property
    def task(self) -> asyncio.Task[None] | None:
        return self._task

    def start(self) -> asyncio.Task[None]:
        if self._task is not None and not self._task.done():
            return self._task
        self._stopped.clear()
        self._task = asyncio.create_task(self._run(), name=f"kafka-worker:{self._name}")
        return self._task

    async def stop(self) -> None:
        self._stopped.set()
        task = self._task
        if task is None:
            return
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        self._task = None

    async def _run(self) -> None:
        try:
            while not self._stopped.is_set():
                try:
                    consumed = await asyncio.wait_for(self._consumer.get(), timeout=0.5)
                except TimeoutError:
                    continue
                except asyncio.CancelledError:
                    raise
                await self._process(consumed)
        except asyncio.CancelledError:
            logger.info(
                "kafka worker cancelled",
                extra=structured_extra(
                    event="kafka.consumer.stopping",
                    source="kafka.worker",
                    worker=self._name,
                ),
            )
            raise
        except Exception:
            logger.error(
                "kafka worker failed",
                exc_info=True,
                extra=structured_extra(
                    event="kafka.worker.failed",
                    source="kafka.worker",
                    worker=self._name,
                ),
            )
            raise

    async def _process(self, consumed: ConsumedEvent) -> None:
        last_error: EventProcessingError | None = None
        for attempt in range(1, self._retry.max_attempts + 1):
            try:
                await self._handler.handle(consumed.envelope)
                await self._consumer.commit(consumed)
                logger.info(
                    "kafka event processed",
                    extra=structured_extra(
                        event="kafka.event.processed",
                        source="kafka.worker",
                        event_id=str(consumed.envelope.event_id),
                        event_type=consumed.envelope.event_type,
                        topic=consumed.topic,
                        partition=consumed.partition,
                        offset=consumed.offset,
                        attempt=attempt,
                    ),
                )
                return
            except Exception as exc:
                last_error = EventProcessingError(str(exc) or "handler failed")
                logger.warning(
                    "kafka event handler failed",
                    extra=structured_extra(
                        event="kafka.event.failed",
                        source="kafka.worker",
                        event_id=str(consumed.envelope.event_id),
                        event_type=consumed.envelope.event_type,
                        topic=consumed.topic,
                        partition=consumed.partition,
                        offset=consumed.offset,
                        attempt=attempt,
                        error_code=last_error.code,
                    ),
                )
                if attempt >= self._retry.max_attempts:
                    break
                delay = self._retry.delay_for_attempt(attempt)
                logger.warning(
                    "kafka event retrying",
                    extra=structured_extra(
                        event="kafka.event.retrying",
                        source="kafka.worker",
                        event_id=str(consumed.envelope.event_id),
                        attempt=attempt,
                        delay_seconds=delay,
                    ),
                )
                await self._sleeper(delay)

        assert last_error is not None
        if self._dlq is not None:
            try:
                await self._dlq.publish_failed(
                    consumed,
                    last_error,
                    self._retry.max_attempts,
                )
            except DlqUnavailableError:
                raise EventRetryExhaustedError(
                    "retry exhausted and DLQ unavailable; offset not committed"
                ) from last_error
            # Even after DLQ success, do not commit — fail closed for #208A.
            raise EventRetryExhaustedError(
                "retry exhausted after DLQ publish; offset not committed"
            ) from last_error
        raise EventRetryExhaustedError(
            "retry exhausted and no DLQ configured; offset not committed"
        ) from last_error
