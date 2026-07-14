"""Kafka-backed PublishPort adapter for market-data orchestration (#306).

Bridges infrastructure-neutral PublishPort to Sprint 2 EventProducer without
Kafka or EventEnvelope leakage into the orchestrator package.

Semantics:
- at-least-once delivery (broker acknowledgement)
- ``idempotency_acknowledged=True`` means the broker accepted a record with the
  deterministic idempotency key — not exactly-once or consumer-side idempotency
- no application-level retry layer (producer/runtime owns retries if any)
"""

from __future__ import annotations

from app.core.clock import Clock
from app.events.envelope import EventEnvelope
from app.events.errors import (
    EventSerializationError,
    KafkaNotConfiguredError,
    KafkaPublishFailedError,
)
from app.events.ports import EventProducer
from app.events.ports import PublishResult as KafkaPublishResult
from app.events.topics import KafkaTopic, TopicRegistry
from app.market_data.enums import MarketEventType
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.keys import build_idempotency_key
from app.market_data.orchestrator.context import PipelineContext
from app.market_data.orchestrator.ports import PublishResult
from app.market_data.serialization import market_event_to_envelope

# Explicit approved orchestrator routing keys → single market-data topic.
_APPROVED_ROUTING_KEYS: frozenset[str] = frozenset(
    f"market.{event_type.value}" for event_type in MarketEventType
)


class KafkaPublishAdapterError(Exception):
    """Typed publish-adapter failure (safe for orchestrator error classification)."""

    code: str = "kafka_publish.error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code


class KafkaPublishUnknownRouteError(KafkaPublishAdapterError):
    code = "kafka_publish.unknown_route"


class KafkaPublishIdempotencyMismatchError(KafkaPublishAdapterError):
    code = "kafka_publish.idempotency_key_mismatch"


class KafkaPublishAdapter:
    """Infrastructure PublishPort implementation backed by EventProducer.

    Does not own producer lifecycle — ``KafkaRuntime`` starts/stops the producer.
    """

    def __init__(
        self,
        *,
        producer: EventProducer,
        topic_registry: TopicRegistry,
        clock: Clock | None = None,
    ) -> None:
        self._producer = producer
        self._topics = topic_registry
        self._clock = clock

    @staticmethod
    def topic_for_routing_key(routing_key: str) -> KafkaTopic:
        """Map a canonical routing key to a Kafka topic. Rejects unknowns."""
        if routing_key not in _APPROVED_ROUTING_KEYS:
            msg = f"unknown market-data routing key: {routing_key!r}"
            raise KafkaPublishUnknownRouteError(msg)
        return KafkaTopic.MARKET_DATA

    @staticmethod
    def approved_routing_keys() -> frozenset[str]:
        return _APPROVED_ROUTING_KEYS

    async def publish(
        self,
        event: CanonicalMarketEvent,
        *,
        routing_key: str,
        context: PipelineContext,
    ) -> PublishResult:
        topic = self.topic_for_routing_key(routing_key)
        # Resolve through registry so prefix environments are validated early.
        resolved_topic_name = self._topics.resolve(topic)

        canonical_key = build_idempotency_key(event)
        if context.idempotency_key is not None and context.idempotency_key != canonical_key:
            raise KafkaPublishIdempotencyMismatchError(
                "context idempotency_key does not match canonical event key"
            )

        try:
            envelope: EventEnvelope = market_event_to_envelope(
                event,
                correlation_id=context.correlation_id,
            )
        except (TypeError, ValueError, EventSerializationError) as exc:
            raise KafkaPublishAdapterError(
                "canonical event envelope conversion failed",
                code="kafka_publish.serialization_failed",
            ) from exc

        if envelope.idempotency_key != canonical_key:
            raise KafkaPublishIdempotencyMismatchError(
                "envelope idempotency_key does not match canonical event key"
            )

        # Deterministic Kafka record key — never a random UUID.
        record_key = context.idempotency_key or canonical_key

        try:
            kafka_result: KafkaPublishResult = await self._producer.publish(
                topic,
                envelope,
                key=record_key,
            )
        except KafkaNotConfiguredError:
            raise
        except KafkaPublishFailedError:
            raise
        except EventSerializationError as exc:
            raise KafkaPublishAdapterError(
                "event serialization failed",
                code="kafka_publish.serialization_failed",
            ) from exc
        except Exception as exc:
            raise KafkaPublishAdapterError(
                "kafka publish failed",
                code="kafka_publish.failed",
            ) from exc

        published_at = kafka_result.timestamp
        if published_at is None and self._clock is not None:
            published_at = self._clock.now()
        if published_at is None:
            published_at = context.received_at
        if published_at.tzinfo is None:
            raise KafkaPublishAdapterError(
                "published_at must be timezone-aware",
                code="kafka_publish.invalid_timestamp",
            )

        # Prefer registry-resolved name when producer returns a topic string;
        # Fake/Aiokafka producers already return the resolved broker topic.
        topic_name = kafka_result.topic or resolved_topic_name
        sink_message_id = f"{topic_name}:{kafka_result.partition}:{kafka_result.offset}"

        return PublishResult(
            succeeded=True,
            published_at=published_at,
            sink_message_id=sink_message_id,
            # Broker acknowledgement for the deterministic record key only.
            idempotency_acknowledged=True,
            safe_metadata={
                "topic": topic_name,
                "partition": str(kafka_result.partition),
                "offset": str(kafka_result.offset),
            },
        )
