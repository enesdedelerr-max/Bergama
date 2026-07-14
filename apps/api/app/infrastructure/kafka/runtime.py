"""Kafka runtime lifecycle owned by the application container."""

from __future__ import annotations

from collections.abc import Sequence

from app.core.kafka_settings import KafkaSettings
from app.core.logging import get_logger, structured_extra
from app.events.ports import EventHandler
from app.events.retry import RetryPolicy
from app.events.topics import TopicRegistry
from app.events.worker import ConsumerWorker
from app.infrastructure.kafka.consumer import AiokafkaEventConsumer
from app.infrastructure.kafka.producer import AiokafkaEventProducer

logger = get_logger(__name__)


class KafkaRuntime:
    """Starts/stops producer, consumers and workers in deterministic order."""

    def __init__(
        self,
        *,
        settings: KafkaSettings,
        topic_registry: TopicRegistry,
        producer: AiokafkaEventProducer | None,
        consumers: Sequence[AiokafkaEventConsumer],
        workers: Sequence[ConsumerWorker],
    ) -> None:
        self.settings = settings
        self.topic_registry = topic_registry
        self.producer = producer
        self.consumers = tuple(consumers)
        self.workers = tuple(workers)
        self._started = False

    @property
    def started(self) -> bool:
        return self._started

    async def start(self) -> None:
        if not self.settings.enabled:
            return
        if self._started:
            return
        try:
            if self.producer is not None:
                await self.producer.start()
            for consumer in self.consumers:
                await consumer.start()
            for worker in self.workers:
                worker.start()
            self._started = True
        except Exception:
            await self.stop()
            raise

    async def stop(self) -> None:
        # Shutdown order: workers → consumers → producer
        for worker in self.workers:
            try:
                await worker.stop()
            except Exception:
                logger.error(
                    "kafka worker stop failed",
                    exc_info=True,
                    extra=structured_extra(
                        event="kafka.shutdown_failed",
                        source="kafka.runtime",
                    ),
                )
        for consumer in self.consumers:
            try:
                await consumer.stop()
            except Exception:
                logger.error(
                    "kafka consumer stop failed",
                    exc_info=True,
                    extra=structured_extra(
                        event="kafka.shutdown_failed",
                        source="kafka.runtime",
                    ),
                )
        if self.producer is not None:
            try:
                await self.producer.stop()
            except Exception:
                logger.error(
                    "kafka producer stop failed",
                    exc_info=True,
                    extra=structured_extra(
                        event="kafka.shutdown_failed",
                        source="kafka.runtime",
                    ),
                )
        self._started = False

    async def fetch_metadata(self) -> object:
        """Cluster metadata for health checks."""
        if self.producer is not None and self.producer.raw_producer is not None:
            return await self.producer.raw_producer.client.fetch_all_metadata()
        for consumer in self.consumers:
            raw = consumer.raw_consumer
            if raw is not None:
                client = getattr(raw, "client", None) or getattr(raw, "_client", None)
                if client is None:
                    break
                return await client.fetch_all_metadata()
        msg = "kafka client is not started"
        raise RuntimeError(msg)


def build_kafka_runtime(
    settings: KafkaSettings,
    *,
    handler: EventHandler | None = None,
    retry_policy: RetryPolicy | None = None,
) -> KafkaRuntime | None:
    """Build Kafka runtime components when enabled; otherwise return None."""
    if not settings.enabled:
        return None
    registry = TopicRegistry(topic_prefix=settings.topic_prefix)
    producer: AiokafkaEventProducer | None = None
    if settings.producer_enabled:
        producer = AiokafkaEventProducer(settings, registry)
    consumers: list[AiokafkaEventConsumer] = []
    workers: list[ConsumerWorker] = []
    if settings.consumer_enabled:
        if handler is None:
            msg = "EventHandler is required when kafka consumer_enabled=true"
            raise ValueError(msg)
        consumer = AiokafkaEventConsumer(
            settings,
            registry,
            topics=list(settings.consumer_topics),
        )
        consumers.append(consumer)
        workers.append(
            ConsumerWorker(
                consumer=consumer,
                handler=handler,
                retry_policy=retry_policy or RetryPolicy(),
                name="primary",
            )
        )
    return KafkaRuntime(
        settings=settings,
        topic_registry=registry,
        producer=producer,
        consumers=consumers,
        workers=workers,
    )
