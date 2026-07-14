"""Optional live Kafka publish smoke for #306.

Environment:
  BERGAMA_KAFKA_PUBLISH_SMOKE=1
  BERGAMA_KAFKA__ENABLED=true
  BERGAMA_KAFKA__BOOTSTRAP_SERVERS=...
  BERGAMA_KAFKA_PUBLISH_SMOKE_TOPIC=market-data  # must already exist; never auto-created
"""

from __future__ import annotations

import os

import pytest
from app.core.clock import SystemClock
from app.core.kafka_settings import KafkaSettings
from app.events.topics import KafkaTopic, TopicRegistry
from app.infrastructure.kafka.market_data_publish import KafkaPublishAdapter
from app.infrastructure.kafka.producer import AiokafkaEventProducer
from app.market_data.keys import build_idempotency_key
from app.market_data.orchestrator.context import PipelineContext
from app.market_data.orchestrator.policies import PipelineDecision
from app.market_data.orchestrator.routing import routing_key_for
from tests.support.market_data_fixtures import make_trade, source

pytestmark = pytest.mark.kafka_integration


def _smoke_enabled() -> bool:
    return os.environ.get("BERGAMA_KAFKA_PUBLISH_SMOKE", "").strip() == "1"


@pytest.mark.asyncio
async def test_live_kafka_publish_adapter_ack() -> None:
    if not _smoke_enabled():
        pytest.skip("BERGAMA_KAFKA_PUBLISH_SMOKE!=1; live Kafka publish smoke skipped")

    servers = os.environ.get("BERGAMA_KAFKA__BOOTSTRAP_SERVERS", "").strip()
    if not servers:
        pytest.fail("BERGAMA_KAFKA__BOOTSTRAP_SERVERS required for kafka publish smoke")

    topic_name = (
        os.environ.get("BERGAMA_KAFKA_PUBLISH_SMOKE_TOPIC", "market-data").strip() or "market-data"
    )
    try:
        topic = KafkaTopic(topic_name)
    except ValueError:
        pytest.fail(
            f"smoke topic {topic_name!r} must be a known KafkaTopic "
            "(market-data|events|audit|execution|risk); provision it before running"
        )
    if topic is not KafkaTopic.MARKET_DATA:
        pytest.fail("BERGAMA_KAFKA_PUBLISH_SMOKE_TOPIC must be market-data for #306")

    settings = KafkaSettings(
        enabled=True,
        bootstrap_servers=[s.strip() for s in servers.split(",") if s.strip()],
        producer_enabled=True,
        consumer_enabled=False,
        enable_auto_commit=False,
    )
    registry = TopicRegistry()
    producer = AiokafkaEventProducer(settings, registry)
    clock = SystemClock()
    adapter = KafkaPublishAdapter(producer=producer, topic_registry=registry, clock=clock)
    event = make_trade(source=source(source_event_id=f"smoke-306-{clock.now().isoformat()}"))
    ctx = PipelineContext(
        event=event,
        dedup_key=f"dedup:{build_idempotency_key(event)}",
        idempotency_key=build_idempotency_key(event),
        routing_key=routing_key_for(event),
        decision=PipelineDecision.ACCEPTED,
        quality=event.quality,
        received_at=clock.now(),
        pipeline_clock=clock,
        correlation_id="smoke-306",
        audit=(),
    )
    try:
        await producer.start()
        result = await adapter.publish(event, routing_key=routing_key_for(event), context=ctx)
    finally:
        await producer.stop()

    assert result.succeeded is True
    assert result.idempotency_acknowledged is True
    assert result.safe_metadata["topic"] == registry.resolve(KafkaTopic.MARKET_DATA)
    assert result.sink_message_id is not None
