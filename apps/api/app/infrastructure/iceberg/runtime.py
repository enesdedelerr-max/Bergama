"""Factory for IcebergWriterRuntime (#307)."""

from __future__ import annotations

from app.core.clock import Clock
from app.core.config import AppSettings
from app.core.environment import AppEnvironment
from app.core.iceberg_writer_settings import IcebergWriterSettings
from app.core.kafka_settings import KafkaSettings
from app.events.topics import KafkaTopic, TopicRegistry
from app.infrastructure.iceberg.catalog import (
    build_catalog,
    ensure_market_tables,
    require_tables_present,
)
from app.infrastructure.iceberg.consumer import IcebergWriterRuntime, IcebergWriterWorker
from app.infrastructure.iceberg.errors import IcebergConfigurationError
from app.infrastructure.iceberg.idempotency import CommittedKeyIndex
from app.infrastructure.iceberg.writer import IcebergTableWriter
from app.infrastructure.kafka.consumer import AiokafkaEventConsumer


def build_iceberg_writer_runtime(
    settings: AppSettings,
    *,
    clock: Clock,
    topic_registry: TopicRegistry | None = None,
    consumer: object | None = None,
) -> IcebergWriterRuntime | None:
    """Construct runtime when enabled. Performs no writes."""
    writer_settings = settings.iceberg_writer
    if not writer_settings.enabled:
        return None
    if not settings.kafka.enabled:
        raise IcebergConfigurationError("iceberg writer requires BERGAMA_KAFKA__ENABLED=true")
    if writer_settings.auto_create_tables and settings.environment not in {
        AppEnvironment.LOCAL,
        AppEnvironment.TEST,
    }:
        raise IcebergConfigurationError(
            "auto_create_tables is only allowed in local/test environments"
        )

    registry = topic_registry or TopicRegistry(topic_prefix=settings.kafka.topic_prefix)
    catalog = build_catalog(writer_settings)
    if writer_settings.auto_create_tables:
        ensure_market_tables(catalog, writer_settings, environment=settings.environment)
    else:
        require_tables_present(catalog, writer_settings)

    resolved_consumer = consumer
    if resolved_consumer is None:
        resolved_consumer = _build_dedicated_consumer(settings.kafka, registry, writer_settings)

    table_writer = IcebergTableWriter(catalog, writer_settings)
    keys = CommittedKeyIndex(
        clock=clock,
        ttl_seconds=writer_settings.committed_key_ttl_seconds,
        max_entries=writer_settings.committed_key_max_entries,
    )
    worker = IcebergWriterWorker(
        consumer=resolved_consumer,  # type: ignore[arg-type]
        table_writer=table_writer,
        settings=writer_settings,
        committed_keys=keys,
        clock=clock,
    )
    return IcebergWriterRuntime(worker=worker, catalog=catalog, settings=writer_settings)


def _build_dedicated_consumer(
    kafka: KafkaSettings,
    registry: TopicRegistry,
    writer_settings: IcebergWriterSettings,
) -> AiokafkaEventConsumer:
    # Clone consumer settings with dedicated group — do not rely on kafka.consumer_enabled.
    consumer_settings = kafka.model_copy(
        update={
            "consumer_enabled": True,
            "consumer_group_id": writer_settings.consumer_group_id,
            "consumer_topics": [KafkaTopic.MARKET_DATA.value],
            "enable_auto_commit": False,
        }
    )
    return AiokafkaEventConsumer(
        consumer_settings,
        registry,
        topics=[KafkaTopic.MARKET_DATA.value],
    )
