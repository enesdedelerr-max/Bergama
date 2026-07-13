"""Optional live Kafka smoke — skipped unless explicitly enabled.

Environment:
  BERGAMA_KAFKA_SMOKE=1
  BERGAMA_KAFKA__ENABLED=true
  BERGAMA_KAFKA__BOOTSTRAP_SERVERS=...
  BERGAMA_KAFKA_SMOKE_TOPIC=events   # must already exist; never auto-created
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.core.kafka_settings import KafkaSettings
from app.events.envelope import EventEnvelope
from app.events.topics import KafkaTopic, TopicRegistry
from app.infrastructure.kafka.consumer import AiokafkaEventConsumer
from app.infrastructure.kafka.producer import AiokafkaEventProducer

pytestmark = pytest.mark.kafka_integration


def _smoke_enabled() -> bool:
    return os.environ.get("BERGAMA_KAFKA_SMOKE", "").strip() == "1"


@pytest.mark.asyncio
async def test_live_kafka_publish_consume_commit_roundtrip() -> None:
    if not _smoke_enabled():
        pytest.skip("BERGAMA_KAFKA_SMOKE!=1; live Kafka smoke skipped")

    servers = os.environ.get("BERGAMA_KAFKA__BOOTSTRAP_SERVERS", "").strip()
    if not servers:
        pytest.fail("BERGAMA_KAFKA__BOOTSTRAP_SERVERS required for live smoke")

    topic_name = os.environ.get("BERGAMA_KAFKA_SMOKE_TOPIC", "events").strip() or "events"
    settings = KafkaSettings(
        enabled=True,
        bootstrap_servers=[s.strip() for s in servers.split(",") if s.strip()],
        producer_enabled=True,
        consumer_enabled=True,
        enable_auto_commit=False,
        consumer_group_id=f"bergama-smoke-{uuid4().hex[:8]}",
        consumer_topics=[topic_name],
        auto_offset_reset="earliest",
    )
    registry = TopicRegistry()
    # Smoke topic must be a known KafkaTopic value; never auto-create.
    try:
        topic = KafkaTopic(topic_name)
    except ValueError:
        pytest.fail(
            f"smoke topic {topic_name!r} must be a known KafkaTopic "
            "(market-data|events|audit|execution|risk); provision it before running"
        )

    producer = AiokafkaEventProducer(settings, registry)
    consumer = AiokafkaEventConsumer(
        settings,
        registry,
        topics=[topic.value],
    )
    event = EventEnvelope(
        event_id=uuid4(),
        event_type="smoke.event",
        schema_version="1",
        source_system="bergama-api-smoke",
        occurred_at=datetime.now(UTC),
        ingested_at=datetime.now(UTC),
        idempotency_key=f"smoke-{uuid4()}",
        payload={"smoke": True},
    )
    try:
        await producer.start()
        await consumer.start()
        published = await producer.publish(topic, event)
        consumed = await consumer.get()
        assert consumed.envelope.event_id == event.event_id
        assert consumed.topic == published.topic
        await consumer.commit(consumed)
    finally:
        await consumer.stop()
        await producer.stop()
