"""Append-only Iceberg table writer (#307).

Multi-table snapshot commits are NOT one atomic transaction. Earlier tables may
already have snapshots if a later table fails. Kafka offsets stay uncommitted and
the process-local committed-key index is not updated on failure.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import pyarrow as pa
from pyiceberg.catalog import Catalog

from app.core.iceberg_writer_settings import IcebergWriterSettings
from app.infrastructure.iceberg.batch import BatchItem
from app.infrastructure.iceberg.catalog import load_required_table
from app.infrastructure.iceberg.errors import (
    IcebergAppendError,
    IcebergParquetError,
    IcebergSnapshotError,
)
from app.infrastructure.iceberg.schemas import DECIMAL_PRECISION, DECIMAL_SCALE, schema_for_table


class IcebergTableWriter:
    """Append PyArrow rows to Iceberg tables and commit one snapshot per table."""

    def __init__(self, catalog: Catalog, settings: IcebergWriterSettings) -> None:
        self._catalog = catalog
        self._settings = settings

    def append_batch(self, items: list[BatchItem]) -> list[str]:
        """Append items grouped by table in stable table-name order.

        Returns the list of table names that received a successful snapshot, in
        commit order. Raises without recording durable Kafka-level success when
        any table fails (prior table snapshots may already exist).
        """
        by_table: dict[str, list[BatchItem]] = defaultdict(list)
        for item in items:
            by_table[item.table_name].append(item)

        committed_tables: list[str] = []
        for table_name in sorted(by_table):
            table_items = by_table[table_name]
            rows = [item.row for item in table_items]
            table_base = _strip_prefix(table_name, self._settings.table_prefix)
            arrow = rows_to_arrow(rows, table_base=table_base)
            table = load_required_table(
                self._catalog,
                namespace=self._settings.namespace,
                table_name=table_name,
            )
            try:
                table.append(arrow)
            except Exception as exc:
                msg = f"Iceberg append/snapshot failed for table {table_name}"
                # pyiceberg append performs the snapshot commit.
                raise IcebergSnapshotError(msg) from exc
            committed_tables.append(table_name)
        return committed_tables


def rows_to_arrow(rows: list[dict[str, Any]], *, table_base: str) -> pa.Table:
    """Build a PyArrow table matching the Iceberg schema field order."""
    if not rows:
        msg = "cannot append empty row set"
        raise IcebergAppendError(msg)
    schema = schema_for_table(table_base)
    try:
        arrays: dict[str, list[Any]] = {field.name: [] for field in schema.fields}
        for row in rows:
            for field in schema.fields:
                arrays[field.name].append(row.get(field.name))
        arrow_fields = [_iceberg_field_to_arrow(field) for field in schema.fields]
        arrow_schema = pa.schema(arrow_fields)
        columns = [
            pa.array(arrays[field.name], type=arrow_field.type)
            for field, arrow_field in zip(schema.fields, arrow_fields, strict=True)
        ]
        return pa.Table.from_arrays(columns, schema=arrow_schema)
    except IcebergParquetError:
        raise
    except Exception as exc:
        msg = "Parquet/Arrow serialization failed"
        raise IcebergParquetError(msg) from exc


def _iceberg_field_to_arrow(field: Any) -> pa.Field:
    from pyiceberg.types import (
        BooleanType,
        DecimalType,
        LongType,
        StringType,
        TimestamptzType,
    )

    ice_type = field.field_type
    nullable = not field.required
    if isinstance(ice_type, StringType):
        pa_type: pa.DataType = pa.string()
    elif isinstance(ice_type, BooleanType):
        pa_type = pa.bool_()
    elif isinstance(ice_type, LongType):
        pa_type = pa.int64()
    elif isinstance(ice_type, TimestamptzType):
        pa_type = pa.timestamp("us", tz="UTC")
    elif isinstance(ice_type, DecimalType):
        pa_type = pa.decimal128(DECIMAL_PRECISION, DECIMAL_SCALE)
    else:
        msg = f"unsupported Iceberg type for field {field.name}"
        raise IcebergParquetError(msg)
    return pa.field(field.name, pa_type, nullable=nullable)


def _strip_prefix(table_name: str, prefix: str) -> str:
    if prefix and table_name.startswith(prefix):
        return table_name[len(prefix) :]
    return table_name
