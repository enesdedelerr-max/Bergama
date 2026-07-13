"""aiokafka EventProducer adapter."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from app.core.kafka_settings import KafkaSettings
from app.core.logging import get_logger, structured_extra
from app.events.envelope import EventEnvelope
from app.events.errors import (
    KafkaNotConfiguredError,
    KafkaPublishFailedError,
    KafkaStartFailedError,
)
from app.events.ports import PublishResult
from app.events.serialization import serialize_event
from app.events.topics import KafkaTopic, TopicRegistry

logger = get_logger(__name__)


class AiokafkaEventProducer:
    """Container-owned Kafka producer. No per-request instances."""

    def __init__(
        self,
        settings: KafkaSettings,
        topic_registry: TopicRegistry,
        *,
        producer_factory: Any | None = None,
    ) -> None:
        self._settings = settings
        self._topics = topic_registry
        self._producer_factory = producer_factory or AIOKafkaProducer
        self._producer: AIOKafkaProducer | None = None
        self._started = False

    @property
    def started(self) -> bool:
        return self._started

    @property
    def raw_producer(self) -> AIOKafkaProducer | None:
        return self._producer

    async def start(self) -> None:
        if self._started:
            return
        if not self._settings.enabled or not self._settings.producer_enabled:
            raise KafkaNotConfiguredError("kafka producer is not enabled")
        logger.info(
            "kafka producer starting",
            extra=structured_extra(event="kafka.producer.starting", source="kafka.producer"),
        )
        try:
            producer = self._producer_factory(
                bootstrap_servers=self._settings.bootstrap_servers,
                client_id=f"{self._settings.client_id}-producer",
                acks=self._settings.acks,
                request_timeout_ms=int(self._settings.request_timeout_seconds * 1000),
                metadata_max_age_ms=int(self._settings.metadata_max_age_seconds * 1000),
            )
            await producer.start()
        except Exception as exc:
            raise KafkaStartFailedError("kafka producer start failed") from exc
        self._producer = producer
        self._started = True
        logger.info(
            "kafka producer started",
            extra=structured_extra(event="kafka.producer.started", source="kafka.producer"),
        )

    async def publish(
        self,
        topic: KafkaTopic,
        event: EventEnvelope,
        *,
        key: str | bytes | None = None,
    ) -> PublishResult:
        if not self._started or self._producer is None:
            raise KafkaNotConfiguredError("kafka producer is not started")
        topic_name = self._topics.resolve(topic)
        body = serialize_event(event)
        encoded_key: bytes | None
        if key is None:
            encoded_key = str(event.idempotency_key).encode("utf-8")
        elif isinstance(key, bytes):
            encoded_key = key
        else:
            encoded_key = key.encode("utf-8")
        try:
            meta = await self._producer.send_and_wait(topic_name, value=body, key=encoded_key)
        except KafkaError as exc:
            raise KafkaPublishFailedError("kafka publish failed") from exc
        except Exception as exc:
            raise KafkaPublishFailedError("kafka publish failed") from exc
        ts: datetime | None = None
        if meta.timestamp is not None:
            ts = datetime.fromtimestamp(meta.timestamp / 1000.0, tz=UTC)
        result = PublishResult(
            topic=topic_name,
            partition=int(meta.partition),
            offset=int(meta.offset),
            timestamp=ts,
        )
        logger.info(
            "kafka event published",
            extra=structured_extra(
                event="kafka.event.published",
                source="kafka.producer",
                event_id=str(event.event_id),
                event_type=event.event_type,
                topic=result.topic,
                partition=result.partition,
                offset=result.offset,
                correlation_id=event.correlation_id,
                causation_id=event.causation_id,
            ),
        )
        return result

    async def stop(self) -> None:
        if not self._started:
            return
        logger.info(
            "kafka producer stopping",
            extra=structured_extra(event="kafka.producer.stopping", source="kafka.producer"),
        )
        producer = self._producer
        self._producer = None
        self._started = False
        if producer is not None:
            await producer.stop()
        logger.info(
            "kafka producer stopped",
            extra=structured_extra(event="kafka.producer.stopped", source="kafka.producer"),
        )
