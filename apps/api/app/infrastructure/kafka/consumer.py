"""aiokafka EventConsumer adapter with manual commit."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aiokafka import AIOKafkaConsumer, TopicPartition
from aiokafka.errors import KafkaError

from app.core.kafka_settings import KafkaSettings
from app.core.logging import get_logger, structured_extra
from app.events.errors import (
    EventDeserializationError,
    KafkaCommitFailedError,
    KafkaConsumeFailedError,
    KafkaNotConfiguredError,
    KafkaStartFailedError,
)
from app.events.ports import ConsumedEvent
from app.events.serialization import deserialize_event
from app.events.topics import TopicRegistry

logger = get_logger(__name__)


class AiokafkaEventConsumer:
    """Container-owned Kafka consumer. enable_auto_commit is always false."""

    def __init__(
        self,
        settings: KafkaSettings,
        topic_registry: TopicRegistry,
        *,
        topics: list[str],
        consumer_factory: Any | None = None,
    ) -> None:
        self._settings = settings
        self._topics = topic_registry
        self._topic_names = topic_registry.resolve_many(topics)
        self._consumer_factory = consumer_factory or AIOKafkaConsumer
        self._consumer: AIOKafkaConsumer | None = None
        self._started = False

    @property
    def started(self) -> bool:
        return self._started

    @property
    def raw_consumer(self) -> AIOKafkaConsumer | None:
        return self._consumer

    async def start(self) -> None:
        if self._started:
            return
        if not self._settings.enabled or not self._settings.consumer_enabled:
            raise KafkaNotConfiguredError("kafka consumer is not enabled")
        if self._settings.enable_auto_commit:
            raise KafkaStartFailedError("enable_auto_commit must be false")
        logger.info(
            "kafka consumer starting",
            extra=structured_extra(
                event="kafka.consumer.starting",
                source="kafka.consumer",
                topics=list(self._topic_names),
            ),
        )
        try:
            consumer = self._consumer_factory(
                *self._topic_names,
                bootstrap_servers=self._settings.bootstrap_servers,
                client_id=f"{self._settings.client_id}-consumer",
                group_id=self._settings.consumer_group_id,
                enable_auto_commit=False,
                auto_offset_reset=self._settings.auto_offset_reset,
                request_timeout_ms=int(self._settings.request_timeout_seconds * 1000),
                session_timeout_ms=int(self._settings.session_timeout_seconds * 1000),
                heartbeat_interval_ms=int(self._settings.heartbeat_interval_seconds * 1000),
                metadata_max_age_ms=int(self._settings.metadata_max_age_seconds * 1000),
                max_poll_records=self._settings.max_poll_records,
            )
            await consumer.start()
        except Exception as exc:
            raise KafkaStartFailedError("kafka consumer start failed") from exc
        self._consumer = consumer
        self._started = True
        logger.info(
            "kafka consumer started",
            extra=structured_extra(event="kafka.consumer.started", source="kafka.consumer"),
        )

    async def get(self) -> ConsumedEvent:
        if not self._started or self._consumer is None:
            raise KafkaNotConfiguredError("kafka consumer is not started")
        try:
            message = await self._consumer.getone()
        except KafkaError as exc:
            raise KafkaConsumeFailedError("kafka consume failed") from exc
        except Exception as exc:
            raise KafkaConsumeFailedError("kafka consume failed") from exc
        try:
            envelope = deserialize_event(message.value or b"")
        except EventDeserializationError:
            raise
        except Exception as exc:
            raise EventDeserializationError("event deserialization failed") from exc
        headers: dict[str, str] = {}
        for key, value in message.headers or ():
            headers[str(key)] = value.decode("utf-8", errors="replace") if value else ""
        ts: datetime | None = None
        if message.timestamp is not None:
            ts = datetime.fromtimestamp(message.timestamp / 1000.0, tz=UTC)
        consumed = ConsumedEvent(
            envelope=envelope,
            topic=str(message.topic),
            partition=int(message.partition),
            offset=int(message.offset),
            timestamp=ts,
            key=message.key,
            headers=headers,
        )
        logger.info(
            "kafka event received",
            extra=structured_extra(
                event="kafka.event.received",
                source="kafka.consumer",
                event_id=str(envelope.event_id),
                event_type=envelope.event_type,
                topic=consumed.topic,
                partition=consumed.partition,
                offset=consumed.offset,
                correlation_id=envelope.correlation_id,
                causation_id=envelope.causation_id,
            ),
        )
        return consumed

    async def commit(self, event: ConsumedEvent) -> None:
        if not self._started or self._consumer is None:
            raise KafkaNotConfiguredError("kafka consumer is not started")
        tp = TopicPartition(event.topic, event.partition)
        try:
            await self._consumer.commit({tp: event.offset + 1})
        except KafkaError as exc:
            raise KafkaCommitFailedError("kafka commit failed") from exc
        except Exception as exc:
            raise KafkaCommitFailedError("kafka commit failed") from exc

    async def stop(self) -> None:
        if not self._started:
            return
        logger.info(
            "kafka consumer stopping",
            extra=structured_extra(event="kafka.consumer.stopping", source="kafka.consumer"),
        )
        consumer = self._consumer
        self._consumer = None
        self._started = False
        if consumer is not None:
            await consumer.stop()
        logger.info(
            "kafka consumer stopped",
            extra=structured_extra(event="kafka.consumer.stopped", source="kafka.consumer"),
        )
