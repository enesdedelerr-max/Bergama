"""Deterministic Iceberg replay ordering (#308).

Order key:
  (occurred_at ASC, event_type ASC, instrument_key ASC, idempotency_key ASC)

This is replay ordering only. Original Kafka partition order cannot be
reconstructed because Kafka topic/partition/offset provenance is not stored
in Iceberg tables.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime

from app.market_data.replay.models import ReplayCursor, ReplayRecord


def replay_order_key(
    occurred_at: datetime,
    event_type: str,
    instrument_key: str,
    idempotency_key: str,
) -> tuple[datetime, str, str, str]:
    return (occurred_at, event_type, instrument_key, idempotency_key)


def sort_replay_records(records: Iterable[ReplayRecord]) -> list[ReplayRecord]:
    """Stable deterministic sort for cross-table merge."""
    return sorted(records, key=lambda r: r.order_key())


def filter_after_cursor(
    records: Sequence[ReplayRecord],
    cursor: ReplayCursor | None,
) -> list[ReplayRecord]:
    """Resume starts strictly after the last successful cursor."""
    if cursor is None:
        return list(records)
    boundary = cursor.as_tuple()
    return [record for record in records if record.order_key() > boundary]
