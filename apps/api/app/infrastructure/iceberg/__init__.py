"""Kafka → Iceberg append-only market-data writer (#307).

Delivery semantics are at-least-once. Iceberg writes are append-only.
Process-local committed-key index may suppress duplicates within a process;
duplicates may reappear after restart. No exactly-once guarantee.
"""

from __future__ import annotations

from app.infrastructure.iceberg.consumer import IcebergWriterRuntime, IcebergWriterWorker
from app.infrastructure.iceberg.errors import IcebergWriterError
from app.infrastructure.iceberg.routing import approved_event_types, table_for_event_type

__all__ = [
    "IcebergWriterError",
    "IcebergWriterRuntime",
    "IcebergWriterWorker",
    "approved_event_types",
    "table_for_event_type",
]
