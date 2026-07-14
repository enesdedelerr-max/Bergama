"""Helpers for Replay Engine offline tests (#308)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.clock import Clock
from app.core.environment import AppEnvironment
from app.core.iceberg_writer_settings import IcebergWriterSettings
from app.core.replay_settings import ReplaySettings
from app.infrastructure.iceberg.catalog import (
    build_catalog,
    build_offline_sql_settings,
    ensure_market_tables,
    load_required_table,
)
from app.infrastructure.iceberg.mapper import map_envelope_to_row
from app.infrastructure.iceberg.replay_source import IcebergReplaySource
from app.infrastructure.iceberg.routing import table_for_event_type
from app.infrastructure.iceberg.writer import rows_to_arrow
from app.infrastructure.replay.file_checkpoint import FileCheckpointStore
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.replay.engine import ReplayEngine, build_replay_engine
from app.market_data.serialization import market_event_to_envelope


def seed_events(
    catalog: object,
    settings: IcebergWriterSettings,
    events: list[CanonicalMarketEvent],
) -> None:
    for event in events:
        envelope = market_event_to_envelope(event)
        row = map_envelope_to_row(envelope, event)
        table_base = table_for_event_type(envelope.event_type)
        table = load_required_table(
            catalog,  # type: ignore[arg-type]
            namespace=settings.namespace,
            table_name=table_base,
        )
        table.append(rows_to_arrow([row], table_base=table_base))


def build_offline_replay_stack(
    tmp_path: Path,
    *,
    clock: Clock,
    events: list[CanonicalMarketEvent] | None = None,
    settings_updates: dict[str, Any] | None = None,
) -> tuple[ReplayEngine, IcebergReplaySource, FileCheckpointStore, IcebergWriterSettings]:
    warehouse = tmp_path / "warehouse"
    writer_settings = build_offline_sql_settings(warehouse)
    catalog = build_catalog(writer_settings)
    ensure_market_tables(catalog, writer_settings, environment=AppEnvironment.TEST)
    if events:
        seed_events(catalog, writer_settings, events)

    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    replay_settings = ReplaySettings(
        enabled=True,
        default_mode="dry_run",
        max_time_range_days=31,
        max_records=10_000,
        checkpoint_enabled=True,
        checkpoint_directory=str(checkpoint_dir.resolve()),
        **(settings_updates or {}),
    )
    source = IcebergReplaySource(catalog, writer_settings)
    store = FileCheckpointStore(checkpoint_dir.resolve())
    engine = build_replay_engine(
        replay_settings,
        clock=clock,
        source=source,
        checkpoint_store=store,
        owns_source=True,
        owns_checkpoint=True,
    )
    return engine, source, store, writer_settings
