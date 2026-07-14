"""Optional live Kafka + Iceberg REST + MinIO smoke (#307).

Enable with: BERGAMA_ICEBERG_WRITER_SMOKE=1

Requires:
- Kafka with pre-created market-data topic
- Iceberg REST catalog
- MinIO / S3-compatible warehouse
- tables pre-created OR BERGAMA_ICEBERG_WRITER__AUTO_CREATE_TABLES=true (local only)

PASS only after snapshot commit and row verification.
"""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime

import pytest
from app.core.clock import SystemClock
from app.core.config import AppSettings
from app.core.environment import AppEnvironment
from app.events.topics import KafkaTopic, TopicRegistry
from app.infrastructure.iceberg.catalog import load_required_table, require_tables_present
from app.infrastructure.iceberg.runtime import build_iceberg_writer_runtime
from app.infrastructure.kafka.producer import AiokafkaEventProducer
from app.market_data.keys import build_idempotency_key
from app.market_data.serialization import market_event_to_envelope
from tests.support.market_data_fixtures import make_quote


def _smoke_enabled() -> bool:
    return os.environ.get("BERGAMA_ICEBERG_WRITER_SMOKE", "").strip() == "1"


pytestmark = pytest.mark.iceberg_writer_smoke


@pytest.mark.asyncio
async def test_live_iceberg_writer_smoke() -> None:
    if not _smoke_enabled():
        pytest.skip("BERGAMA_ICEBERG_WRITER_SMOKE!=1; live Iceberg writer smoke skipped")

    settings = AppSettings()
    if settings.environment not in {AppEnvironment.LOCAL, AppEnvironment.TEST}:
        pytest.fail("live iceberg writer smoke is local/test only")
    if not settings.iceberg_writer.enabled:
        pytest.fail("BERGAMA_ICEBERG_WRITER__ENABLED must be true for live smoke")
    if not settings.kafka.enabled:
        pytest.fail("BERGAMA_KAFKA__ENABLED must be true for live smoke")

    clock = SystemClock()
    registry = TopicRegistry(topic_prefix=settings.kafka.topic_prefix)
    runtime = build_iceberg_writer_runtime(settings, clock=clock, topic_registry=registry)
    assert runtime is not None
    if not settings.iceberg_writer.auto_create_tables:
        require_tables_present(runtime.catalog, settings.iceberg_writer)

    producer = AiokafkaEventProducer(settings.kafka, registry)
    event = make_quote(
        source=make_quote().source.model_copy(
            update={"source_event_id": f"iceberg-smoke-{datetime.now(UTC).isoformat()}"}
        )
    )
    envelope = market_event_to_envelope(event)
    key = build_idempotency_key(event)

    await producer.start()
    try:
        await runtime.start()
        await producer.publish(KafkaTopic.MARKET_DATA, envelope, key=key)
        # Await durability: scan until the idempotency key appears.
        table = load_required_table(
            runtime.catalog,
            namespace=settings.iceberg_writer.namespace,
            table_name=(
                f"{settings.iceberg_writer.table_prefix}market_quotes"
                if settings.iceberg_writer.table_prefix
                else "market_quotes"
            ),
        )
        deadline = asyncio.get_running_loop().time() + 30.0
        found = False
        while asyncio.get_running_loop().time() < deadline:
            rows = table.scan().to_arrow()
            keys = set(rows["idempotency_key"].to_pylist()) if len(rows) else set()
            if key in keys:
                found = True
                break
            await asyncio.sleep(0.25)
        assert found, "Iceberg snapshot/row not observed after publish"
        # Snapshot presence
        assert table.current_snapshot() is not None
    finally:
        await runtime.aclose()
        await producer.stop()
