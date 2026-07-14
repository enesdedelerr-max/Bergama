"""Unit tests for Kafka container ownership when disabled/enabled."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.core.kafka_settings import KafkaSettings
from app.events.retry import RetryPolicy
from app.health.service import build_default_health_checks
from app.infrastructure.kafka.health import KafkaHealthCheck
from app.infrastructure.kafka.producer import AiokafkaEventProducer
from app.infrastructure.kafka.runtime import KafkaRuntime
from app.schemas.health import DependencyHealthStatus


def test_container_creates_no_kafka_clients_when_disabled() -> None:
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        debug=False,
        bootstrap_auth_enabled=False,
        kafka=KafkaSettings(enabled=False),
    )
    container = build_container(settings)
    assert container.kafka_runtime is None
    assert container.topic_registry.resolve("events") == "events"


@pytest.mark.asyncio
async def test_cleanup_order_deterministic() -> None:
    order: list[str] = []

    class TrackingWorker:
        async def stop(self) -> None:
            order.append("worker")

    class TrackingConsumer:
        async def stop(self) -> None:
            order.append("consumer")

    class TrackingProducer:
        async def stop(self) -> None:
            order.append("producer")

    runtime = KafkaRuntime(
        settings=KafkaSettings(enabled=True, bootstrap_servers=["localhost:9092"]),
        topic_registry=build_container(
            AppSettings(environment=AppEnvironment.TEST, bootstrap_auth_enabled=False)
        ).topic_registry,
        producer=TrackingProducer(),  # type: ignore[arg-type]
        consumers=[TrackingConsumer()],  # type: ignore[list-item]
        workers=[TrackingWorker()],  # type: ignore[list-item]
    )
    runtime._started = True  # noqa: SLF001
    await runtime.stop()
    assert order == ["worker", "consumer", "producer"]


@pytest.mark.asyncio
async def test_kafka_health_skipped_when_disabled() -> None:
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        debug=False,
        bootstrap_auth_enabled=False,
        kafka=KafkaSettings(enabled=False),
    )
    checks = build_default_health_checks(settings, kafka_runtime=None)
    kafka_check = next(c for c in checks if getattr(c, "name", None) == "kafka")
    assert isinstance(kafka_check, KafkaHealthCheck)
    result = await kafka_check.check()
    assert result.status is DependencyHealthStatus.SKIPPED


@pytest.mark.asyncio
async def test_kafka_health_fails_if_enabled_but_unavailable() -> None:
    settings = KafkaSettings(
        enabled=True,
        bootstrap_servers=["localhost:9092"],
        health_required=True,
    )
    check = KafkaHealthCheck(
        settings=settings,
        timeout_seconds=1.0,
        metadata_fetcher=None,
    )
    result = await check.check()
    assert result.status is DependencyHealthStatus.FAIL


@pytest.mark.asyncio
async def test_producer_lifecycle_idempotent() -> None:
    settings = KafkaSettings(enabled=True, bootstrap_servers=["localhost:9092"])
    fake = MagicMock()
    fake.start = AsyncMock()
    fake.stop = AsyncMock()
    factory = MagicMock(return_value=fake)
    registry = build_container(
        AppSettings(environment=AppEnvironment.TEST, bootstrap_auth_enabled=False)
    ).topic_registry
    producer = AiokafkaEventProducer(settings, registry, producer_factory=factory)
    await producer.start()
    await producer.start()
    assert fake.start.await_count == 1
    await producer.stop()
    await producer.stop()
    assert fake.stop.await_count == 1


def test_retry_policy_rejects_invalid() -> None:
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)
