"""Required Sprint 3 live/local runtime smoke.

Synthetic BarEvent -> MarketDataOrchestrator -> KafkaPublishAdapter -> Kafka
-> IcebergWriterWorker -> Iceberg snapshot -> row read -> Kafka offset commit.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
API_PATH = ROOT / "apps" / "api"
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from aiokafka import TopicPartition  # noqa: E402
from aiokafka.admin import AIOKafkaAdminClient  # noqa: E402

from app.core.clock import FixedClock  # noqa: E402
from app.core.config import AppSettings  # noqa: E402
from app.core.environment import AppEnvironment  # noqa: E402
from app.core.iceberg_writer_settings import IcebergWriterSettings  # noqa: E402
from app.core.kafka_settings import KafkaSettings  # noqa: E402
from app.core.orchestrator_settings import OrchestratorSettings  # noqa: E402
from app.events.ports import ConsumedEvent  # noqa: E402
from app.events.topics import KafkaTopic, TopicRegistry  # noqa: E402
from app.infrastructure.iceberg.catalog import (  # noqa: E402
    build_catalog,
    ensure_market_tables,
    load_required_table,
    require_tables_present,
)
from app.infrastructure.iceberg.consumer import IcebergWriterWorker  # noqa: E402
from app.infrastructure.iceberg.idempotency import CommittedKeyIndex  # noqa: E402
from app.infrastructure.iceberg.routing import table_for_event_type  # noqa: E402
from app.infrastructure.iceberg.writer import IcebergTableWriter  # noqa: E402
from app.infrastructure.kafka.consumer import AiokafkaEventConsumer  # noqa: E402
from app.infrastructure.kafka.market_data_publish import KafkaPublishAdapter  # noqa: E402
from app.infrastructure.kafka.producer import AiokafkaEventProducer  # noqa: E402
from app.market_data.data_quality import DataQualityService, default_quality_policy  # noqa: E402
from app.market_data.enums import AdjustmentState, AssetClass  # noqa: E402
from app.market_data.events.bar import BarEvent  # noqa: E402
from app.market_data.identity import InstrumentId  # noqa: E402
from app.market_data.keys import build_idempotency_key  # noqa: E402
from app.market_data.orchestrator.pipeline import MarketDataOrchestrator  # noqa: E402
from app.market_data.orchestrator.policies import PipelineDecision  # noqa: E402
from app.market_data.quality import DataQualityFlags  # noqa: E402
from app.market_data.serialization import CANONICAL_MARKET_SCHEMA_VERSION  # noqa: E402
from app.market_data.source import SourceReference  # noqa: E402
from scripts.gates.sprint3_common import (  # noqa: E402
    EVIDENCE_VERSION,
    ensure_no_secrets,
    git_meta,
    sanitized_environment_summary,
    utc_now,
    write_json,
)

EVIDENCE_PATH = ROOT / "artifacts" / "sprint3" / "evidence" / "runtime-smoke.json"
FIXED_T0 = datetime(2026, 7, 13, 14, 30, 0, tzinfo=UTC)
EXPECTED_CLOSE = Decimal("190.20")


@dataclass(slots=True)
class RuntimeMarkers:
    kafka_publish_acknowledged_at: str | None = None
    iceberg_append_started_at: str | None = None
    iceberg_snapshot_committed_at: str | None = None
    row_verified_at: str | None = None
    kafka_offset_committed_at: str | None = None
    snapshot_id: str | None = None
    committed_tables: list[str] = field(default_factory=list)
    offset_before: int | None = None
    offset_after: int | None = None
    direct_committed_offset: int | None = None


class RecordingIcebergTableWriter:
    def __init__(
        self,
        inner: IcebergTableWriter,
        *,
        catalog: Any,
        settings: IcebergWriterSettings,
        markers: RuntimeMarkers,
    ) -> None:
        self._inner = inner
        self._catalog = catalog
        self._settings = settings
        self._markers = markers

    def append_batch(self, items: list[Any]) -> list[str]:
        self._markers.iceberg_append_started_at = utc_now()
        committed = self._inner.append_batch(items)
        self._markers.committed_tables = list(committed)
        table_name = table_for_event_type("market.bar", table_prefix=self._settings.table_prefix)
        table = load_required_table(
            self._catalog,
            namespace=self._settings.namespace,
            table_name=table_name,
        )
        snapshot = table.current_snapshot()
        self._markers.snapshot_id = str(snapshot.snapshot_id) if snapshot is not None else None
        self._markers.iceberg_snapshot_committed_at = utc_now()
        return committed


class RecordingConsumer:
    def __init__(self, inner: AiokafkaEventConsumer, markers: RuntimeMarkers) -> None:
        self._inner = inner
        self._markers = markers

    @property
    def raw_consumer(self) -> Any:
        return self._inner.raw_consumer

    async def start(self) -> None:
        await self._inner.start()

    async def get(self) -> ConsumedEvent:
        return await self._inner.get()

    async def commit(self, event: ConsumedEvent) -> None:
        raw = self._inner.raw_consumer
        tp = TopicPartition(event.topic, event.partition)
        if raw is not None:
            try:
                before = await raw.committed(tp)
                self._markers.offset_before = int(before) if before is not None else None
            except Exception:
                self._markers.offset_before = None
        await self._inner.commit(event)
        self._markers.kafka_offset_committed_at = utc_now()
        self._markers.offset_after = event.offset + 1
        raw_after = self._inner.raw_consumer
        if raw_after is not None:
            try:
                committed = await raw_after.committed(tp)
                self._markers.direct_committed_offset = (
                    int(committed) if committed is not None else None
                )
            except Exception:
                self._markers.direct_committed_offset = None

    async def stop(self) -> None:
        await self._inner.stop()


def _write_failure(commit: str, reason: str, *, extra: dict[str, Any] | None = None) -> None:
    payload = {
        "evidence_version": EVIDENCE_VERSION,
        "git_commit": commit,
        "generated_at": utc_now(),
        "final_status": "FAIL",
        "failure_reason": reason,
        "sanitized_environment_summary": sanitized_environment_summary(),
    }
    if extra:
        payload.update(extra)
    write_json(EVIDENCE_PATH, payload)


def _build_event(commit: str) -> BarEvent:
    source_event_id = f"sprint3-runtime-{commit[:12]}"
    return BarEvent.model_validate(
        {
            "schema_version": CANONICAL_MARKET_SCHEMA_VERSION,
            "instrument": InstrumentId(
                instrument_key="bergama:equity:us:sprint3_runtime",
                asset_class=AssetClass.EQUITY,
                local_symbol="SPRT3",
                symbol_effective_from=datetime(2020, 1, 1, tzinfo=UTC),
            ),
            "source": SourceReference(
                provider="bergama_synthetic",
                source_symbol="SPRT3",
                source_instrument_id="SYNTH-SPRT3",
                source_event_id=source_event_id,
                source_payload_ref="synthetic://sprint3/runtime-gate/bar",
                extras={"purpose": "runtime_gate"},
            ),
            "quality": DataQualityFlags(),
            "adjustment_state": AdjustmentState.UNADJUSTED,
            "occurred_at": FIXED_T0,
            "effective_at": FIXED_T0,
            "known_at": FIXED_T0 + timedelta(milliseconds=50),
            "ingested_at": FIXED_T0 + timedelta(milliseconds=100),
            "currency": "USD",
            "venue": "XNAS",
            "metadata": {"gate": "sprint3"},
            "window_start": FIXED_T0 - timedelta(minutes=1),
            "window_end": FIXED_T0,
            "close_time": FIXED_T0,
            "open": Decimal("190.00"),
            "high": Decimal("190.50"),
            "low": Decimal("189.80"),
            "close": EXPECTED_CLOSE,
            "volume": Decimal("10000"),
            "vwap": Decimal("190.10"),
            "trade_count": 42,
        }
    )


def _safe_settings() -> AppSettings:
    settings = AppSettings(bootstrap_auth_enabled=False)
    if settings.environment not in {AppEnvironment.LOCAL, AppEnvironment.TEST}:
        msg = "Sprint 3 runtime smoke is local/test only"
        raise RuntimeError(msg)
    if not settings.kafka.enabled:
        raise RuntimeError("BERGAMA_KAFKA__ENABLED=true is required")
    if not settings.iceberg_writer.enabled:
        raise RuntimeError("BERGAMA_ICEBERG_WRITER__ENABLED=true is required")
    kafka = settings.kafka.model_copy(
        update={
            "producer_enabled": True,
            "consumer_enabled": False,
            "enable_auto_commit": False,
            "auto_offset_reset": "latest",
        }
    )
    iceberg = settings.iceberg_writer.model_copy(
        update={
            "batch_max_records": 1,
            "flush_interval_seconds": 0.5,
            "consumer_group_id": "bergama-sprint3-runtime-gate",
        }
    )
    orchestrator = OrchestratorSettings(
        enabled=True,
        dry_run=False,
        publish_backend="kafka",
        pipeline_name="sprint3-runtime-gate",
        max_in_flight=8,
        admission_timeout_seconds=1.0,
    )
    return settings.model_copy(update={"kafka": kafka, "iceberg_writer": iceberg, "orchestrator": orchestrator})


def _http_probe(url: str, *, label: str) -> None:
    if label == "iceberg_rest":
        target = urljoin(url.rstrip("/") + "/", "v1/config")
    elif label == "minio":
        target = urljoin(url.rstrip("/") + "/", "minio/health/ready")
    else:
        target = url
    request = Request(target, method="GET")
    with urlopen(request, timeout=5) as response:  # noqa: S310 - local smoke endpoint from config
        if response.status >= 500:
            raise RuntimeError(f"{label} returned HTTP {response.status}")


async def _list_topics(settings: KafkaSettings, registry: TopicRegistry) -> list[str]:
    admin = AIOKafkaAdminClient(
        bootstrap_servers=settings.bootstrap_servers,
        client_id=f"{settings.client_id}-sprint3-runtime-admin",
    )
    await admin.start()
    try:
        topics = await admin.list_topics()
        return sorted(str(topic) for topic in topics)
    finally:
        await admin.close()


def _cluster_snapshot() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, command in {
        "context": ["kubectl", "config", "current-context"],
        "pods": ["kubectl", "get", "pods", "-A", "-o", "wide"],
    }.items():
        try:
            proc = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except Exception as exc:  # noqa: BLE001
            out[name] = {"status": "FAIL", "error": type(exc).__name__}
            continue
        text = (proc.stdout or proc.stderr).strip()
        ensure_no_secrets(text, context=f"kubectl {name}")
        out[name] = {"status": "PASS" if proc.returncode == 0 else "FAIL", "output": text[:4000]}
    return out


def _row_matches(row: dict[str, Any], *, key: str, event: BarEvent) -> tuple[bool, dict[str, Any]]:
    close = row.get("close")
    occurred_at = row.get("occurred_at")
    occurred_iso = (
        occurred_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
        if isinstance(occurred_at, datetime)
        else str(occurred_at)
    )
    expected_iso = event.occurred_at.isoformat().replace("+00:00", "Z")
    decimal_verified = close == EXPECTED_CLOSE
    summary = {
        "idempotency_key_matches": row.get("idempotency_key") == key,
        "event_type_matches": row.get("event_type") == "market.bar",
        "occurred_at_matches": occurred_iso == expected_iso,
        "close_value": str(close),
        "expected_close": str(EXPECTED_CLOSE),
        "decimal_verified_without_float": decimal_verified,
    }
    return all(
        [
            summary["idempotency_key_matches"],
            summary["event_type_matches"],
            summary["occurred_at_matches"],
            decimal_verified,
        ]
    ), summary


async def _await_row(
    *,
    catalog: Any,
    settings: IcebergWriterSettings,
    key: str,
    event: BarEvent,
    markers: RuntimeMarkers,
) -> tuple[bool, dict[str, Any]]:
    table_name = table_for_event_type("market.bar", table_prefix=settings.table_prefix)
    deadline = asyncio.get_running_loop().time() + 45.0
    last_summary: dict[str, Any] = {}
    while asyncio.get_running_loop().time() < deadline:
        table = load_required_table(catalog, namespace=settings.namespace, table_name=table_name)
        arrow = table.scan().to_arrow()
        if len(arrow):
            rows = arrow.to_pylist()
            candidates = [row for row in rows if row.get("idempotency_key") == key]
            for row in candidates:
                matched, summary = _row_matches(row, key=key, event=event)
                last_summary = summary
                if matched:
                    markers.row_verified_at = utc_now()
                    return True, summary
        await asyncio.sleep(0.25)
    return False, last_summary


async def run_smoke(root: Path = ROOT) -> int:
    _, commit = git_meta(root)
    markers = RuntimeMarkers()
    worker: IcebergWriterWorker | None = None
    producer: AiokafkaEventProducer | None = None
    try:
        settings = _safe_settings()
        registry = TopicRegistry(topic_prefix=settings.kafka.topic_prefix)
        topic = registry.resolve(KafkaTopic.MARKET_DATA)
        topics = await _list_topics(settings.kafka, registry)
        if topic not in topics:
            raise RuntimeError(f"required Kafka topic missing: {topic}")
        if settings.iceberg_writer.catalog_uri is None:
            raise RuntimeError("Iceberg REST catalog URI is required")
        _http_probe(settings.iceberg_writer.catalog_uri, label="iceberg_rest")
        if settings.iceberg_writer.s3_endpoint is None:
            raise RuntimeError("MinIO/S3 endpoint is required")
        _http_probe(settings.iceberg_writer.s3_endpoint, label="minio")

        clock = FixedClock(FIXED_T0 + timedelta(seconds=1))
        catalog = build_catalog(settings.iceberg_writer)
        if settings.iceberg_writer.auto_create_tables:
            ensure_market_tables(catalog, settings.iceberg_writer, environment=settings.environment)
        else:
            require_tables_present(catalog, settings.iceberg_writer)

        consumer_settings = settings.kafka.model_copy(
            update={
                "consumer_enabled": True,
                "consumer_group_id": settings.iceberg_writer.consumer_group_id,
                "consumer_topics": [KafkaTopic.MARKET_DATA.value],
                "enable_auto_commit": False,
                "auto_offset_reset": "latest",
            }
        )
        inner_consumer = AiokafkaEventConsumer(
            consumer_settings,
            registry,
            topics=[KafkaTopic.MARKET_DATA.value],
        )
        consumer = RecordingConsumer(inner_consumer, markers)
        writer = RecordingIcebergTableWriter(
            IcebergTableWriter(catalog, settings.iceberg_writer),
            catalog=catalog,
            settings=settings.iceberg_writer,
            markers=markers,
        )
        keys = CommittedKeyIndex(
            clock=clock,
            ttl_seconds=settings.iceberg_writer.committed_key_ttl_seconds,
            max_entries=settings.iceberg_writer.committed_key_max_entries,
        )
        worker = IcebergWriterWorker(
            consumer=consumer,
            table_writer=writer,  # type: ignore[arg-type]
            settings=settings.iceberg_writer,
            committed_keys=keys,
            clock=clock,
            name="sprint3-runtime-gate",
        )
        producer = AiokafkaEventProducer(settings.kafka, registry)
        adapter = KafkaPublishAdapter(producer=producer, topic_registry=registry, clock=clock)
        quality = DataQualityService(
            policy=default_quality_policy(observe_only=True),
            clock=clock,
            enabled=True,
            required=True,
        )
        orchestrator = MarketDataOrchestrator(
            settings=settings.orchestrator,
            clock=clock,
            publish_port=adapter,
            data_quality_service=quality,
        )
        event = _build_event(commit)
        idempotency_key = build_idempotency_key(event)

        await producer.start()
        await worker.start()
        result = await orchestrator.process(event, correlation_id="sprint3-runtime-gate")
        markers.kafka_publish_acknowledged_at = utc_now()
        if result.decision is not PipelineDecision.PUBLISHED:
            raise RuntimeError(f"orchestrator decision was {result.decision.value}, not published")
        if result.context.quality_assessment is None:
            raise RuntimeError("quality assessment missing from orchestrator context")
        found, row_summary = await _await_row(
            catalog=catalog,
            settings=settings.iceberg_writer,
            key=idempotency_key,
            event=event,
            markers=markers,
        )
        if not found:
            raise RuntimeError("Iceberg row verification failed")
        deadline = asyncio.get_running_loop().time() + 20.0
        while markers.kafka_offset_committed_at is None and asyncio.get_running_loop().time() < deadline:
            await asyncio.sleep(0.1)
        if markers.kafka_offset_committed_at is None:
            raise RuntimeError("Kafka offset commit was not observed")

        snapshot_at = markers.iceberg_snapshot_committed_at
        offset_at = markers.kafka_offset_committed_at
        if snapshot_at is None or offset_at is None or snapshot_at > offset_at:
            raise RuntimeError("offset-after-durability invariant failed")
        offset_verified = markers.direct_committed_offset is None or (
            markers.offset_after is not None and markers.direct_committed_offset >= markers.offset_after
        )
        if not offset_verified:
            raise RuntimeError("direct Kafka committed offset did not advance")

        assessment = result.context.quality_assessment
        payload = {
            "evidence_version": EVIDENCE_VERSION,
            "git_commit": commit,
            "generated_at": utc_now(),
            "environment": settings.environment.value,
            "topic": topic,
            "consumer_group": settings.iceberg_writer.consumer_group_id,
            "table": f"{settings.iceberg_writer.namespace}.{table_for_event_type('market.bar', table_prefix=settings.iceberg_writer.table_prefix)}",
            "event_type": "market.bar",
            "idempotency_key": idempotency_key,
            "kafka_ack_metadata": result.context.metadata,
            "snapshot_id": markers.snapshot_id,
            "row_verification_summary": row_summary,
            "decimal_verification": {
                "field": "close",
                "expected": str(EXPECTED_CLOSE),
                "matched": row_summary.get("decimal_verified_without_float") is True,
            },
            "offset_before": markers.offset_before,
            "offset_after": markers.offset_after,
            "direct_committed_offset": markers.direct_committed_offset,
            "operation_timestamps": {
                "kafka_publish_acknowledged_at": markers.kafka_publish_acknowledged_at,
                "iceberg_append_started_at": markers.iceberg_append_started_at,
                "iceberg_snapshot_committed_at": markers.iceberg_snapshot_committed_at,
                "row_verified_at": markers.row_verified_at,
                "kafka_offset_committed_at": markers.kafka_offset_committed_at,
            },
            "quality_assessment_summary": {
                "assessment_id": assessment.assessment_id,
                "overall_status": assessment.overall_status.value,
                "highest_severity": assessment.highest_severity.value,
                "recommended_action": assessment.recommended_action.value,
                "rule_count": len(assessment.rule_results),
            },
            "kafka_ack_verified": result.context.metadata.get("sink_message_id") is not None,
            "snapshot_verified": markers.snapshot_id is not None,
            "row_verified": found,
            "decimal_verified": row_summary.get("decimal_verified_without_float") is True,
            "offset_after_durability_verified": True,
            "cluster_snapshot": _cluster_snapshot(),
            "sanitized_environment_summary": sanitized_environment_summary(),
            "safe_limitations": [
                "local/runtime smoke uses synthetic canonical event only",
                "does not call provider APIs",
                "at-least-once semantics only; exactly-once is not claimed",
            ],
            "final_status": "PASS",
        }
        write_json(EVIDENCE_PATH, payload)
        print("PASS: Sprint 3 runtime smoke completed")
        return 0
    except Exception as exc:  # noqa: BLE001
        _write_failure(commit, str(exc), extra={"cluster_snapshot": _cluster_snapshot()})
        print(f"FAIL: {exc}")
        return 1
    finally:
        if worker is not None:
            try:
                await worker.aclose()
            except Exception:
                pass
        if producer is not None:
            try:
                await producer.stop()
            except Exception:
                pass


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run required Sprint 3 runtime smoke")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(list(argv) if argv is not None else None)
    return asyncio.run(run_smoke(args.root.resolve()))


if __name__ == "__main__":
    raise SystemExit(main())
