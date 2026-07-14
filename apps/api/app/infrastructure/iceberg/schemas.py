"""Version-controlled Iceberg table schemas (#307).

Decimal policy: decimal(38,18) for all financial values.
Partition: day(occurred_at).
idempotency_key is documented as the identifier field (schema metadata only —
Iceberg does not enforce uniqueness under append-only writes).
"""

from __future__ import annotations

from pyiceberg.partitioning import PartitionField, PartitionSpec
from pyiceberg.schema import Schema
from pyiceberg.transforms import DayTransform
from pyiceberg.types import (
    BooleanType,
    DecimalType,
    LongType,
    NestedField,
    StringType,
    TimestamptzType,
)

# Documented fixed decimal policy for Sprint 3 (#307).
DECIMAL_PRECISION = 38
DECIMAL_SCALE = 18
MONEY_DECIMAL = DecimalType(DECIMAL_PRECISION, DECIMAL_SCALE)

SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0.0"})


def _common_fields(*, start_id: int = 1) -> list[NestedField]:
    """Shared columns across all market-data Iceberg tables."""
    i = start_id
    fields = [
        NestedField(i, "event_id", StringType(), required=True),
        NestedField(i + 1, "event_type", StringType(), required=True),
        NestedField(i + 2, "schema_version", StringType(), required=True),
        NestedField(i + 3, "source_system", StringType(), required=True),
        NestedField(i + 4, "occurred_at", TimestamptzType(), required=True),
        NestedField(i + 5, "ingested_at", TimestamptzType(), required=True),
        NestedField(i + 6, "effective_at", TimestamptzType(), required=True),
        NestedField(i + 7, "known_at", TimestamptzType(), required=True),
        NestedField(i + 8, "instrument_key", StringType(), required=True),
        NestedField(i + 9, "asset_class", StringType(), required=True),
        NestedField(i + 10, "local_symbol", StringType(), required=False),
        NestedField(i + 11, "idempotency_key", StringType(), required=True),
        NestedField(i + 12, "deduplication_key", StringType(), required=True),
        NestedField(i + 13, "source_provider", StringType(), required=True),
        NestedField(i + 14, "source_event_id", StringType(), required=False),
        NestedField(i + 15, "correlation_id", StringType(), required=False),
        NestedField(i + 16, "is_late", BooleanType(), required=True),
        NestedField(i + 17, "is_revision", BooleanType(), required=True),
        NestedField(i + 18, "is_stale", BooleanType(), required=True),
        NestedField(i + 19, "is_estimated", BooleanType(), required=True),
        NestedField(i + 20, "is_incomplete", BooleanType(), required=True),
        NestedField(i + 21, "revision_of_event_id", StringType(), required=False),
        NestedField(i + 22, "late_arrival_lag_ms", LongType(), required=False),
        NestedField(i + 23, "adjustment_state", StringType(), required=True),
        NestedField(i + 24, "currency", StringType(), required=False),
        NestedField(i + 25, "venue", StringType(), required=False),
        NestedField(i + 26, "metadata_json", StringType(), required=False),
    ]
    return fields


# Field id of idempotency_key in common layout (1-based start → id 12).
_IDEMPOTENCY_FIELD_ID = 12
_OCCURRED_AT_FIELD_ID = 5


def _schema_with_extras(extras: list[NestedField]) -> Schema:
    common = _common_fields()
    next_id = max(f.field_id for f in common) + 1
    renumbered: list[NestedField] = []
    for offset, field in enumerate(extras):
        renumbered.append(
            NestedField(
                next_id + offset,
                field.name,
                field.field_type,
                required=field.required,
                doc=field.doc,
            )
        )
    return Schema(
        *common,
        *renumbered,
        identifier_field_ids=[_IDEMPOTENCY_FIELD_ID],
    )


def day_partition_spec() -> PartitionSpec:
    return PartitionSpec(
        PartitionField(
            source_id=_OCCURRED_AT_FIELD_ID,
            field_id=1000,
            transform=DayTransform(),
            name="occurred_at_day",
        )
    )


def schema_for_table(table_base: str) -> Schema:
    mapping = {
        "market_quotes": quote_schema,
        "market_trades": trade_schema,
        "market_bars": bar_schema,
        "market_reference_data": reference_schema,
        "market_fundamentals": fundamental_schema,
        "market_macro": macro_schema,
        "market_filings": filing_schema,
        "market_news": news_schema,
    }
    factory = mapping.get(table_base)
    if factory is None:
        msg = f"no Iceberg schema for table {table_base!r}"
        raise ValueError(msg)
    return factory()


def quote_schema() -> Schema:
    return _schema_with_extras(
        [
            NestedField(100, "bid_price", MONEY_DECIMAL, required=True),
            NestedField(101, "bid_size", MONEY_DECIMAL, required=True),
            NestedField(102, "ask_price", MONEY_DECIMAL, required=True),
            NestedField(103, "ask_size", MONEY_DECIMAL, required=True),
        ]
    )


def trade_schema() -> Schema:
    return _schema_with_extras(
        [
            NestedField(100, "price", MONEY_DECIMAL, required=True),
            NestedField(101, "size", MONEY_DECIMAL, required=True),
            NestedField(102, "trade_id", StringType(), required=False),
        ]
    )


def bar_schema() -> Schema:
    return _schema_with_extras(
        [
            NestedField(100, "window_start", TimestamptzType(), required=True),
            NestedField(101, "window_end", TimestamptzType(), required=True),
            NestedField(102, "close_time", TimestamptzType(), required=True),
            NestedField(103, "open", MONEY_DECIMAL, required=True),
            NestedField(104, "high", MONEY_DECIMAL, required=True),
            NestedField(105, "low", MONEY_DECIMAL, required=True),
            NestedField(106, "close", MONEY_DECIMAL, required=True),
            NestedField(107, "volume", MONEY_DECIMAL, required=True),
            NestedField(108, "vwap", MONEY_DECIMAL, required=False),
            NestedField(109, "trade_count", LongType(), required=False),
        ]
    )


def reference_schema() -> Schema:
    return _schema_with_extras(
        [
            NestedField(100, "name", StringType(), required=False),
            NestedField(101, "reference_attributes_json", StringType(), required=False),
        ]
    )


def fundamental_schema() -> Schema:
    return _schema_with_extras(
        [
            NestedField(100, "metric_code", StringType(), required=True),
            NestedField(101, "period", StringType(), required=True),
            NestedField(102, "value", MONEY_DECIMAL, required=True),
            NestedField(103, "unit", StringType(), required=False),
        ]
    )


def macro_schema() -> Schema:
    return _schema_with_extras(
        [
            NestedField(100, "series_id", StringType(), required=True),
            NestedField(101, "value", MONEY_DECIMAL, required=True),
            NestedField(102, "frequency", StringType(), required=False),
            NestedField(103, "provider_units", StringType(), required=False),
        ]
    )


def filing_schema() -> Schema:
    # Canonical FilingEvent provides form_type/accession_number/title/document_ref.
    # Extra design columns are nullable until the contract grows.
    return _schema_with_extras(
        [
            NestedField(100, "form_type", StringType(), required=True),
            NestedField(101, "accession_number", StringType(), required=True),
            NestedField(102, "filing_date", TimestamptzType(), required=False),
            NestedField(103, "report_date", TimestamptzType(), required=False),
            NestedField(104, "filing_url", StringType(), required=False),
            NestedField(105, "is_amendment", BooleanType(), required=True),
            NestedField(106, "title", StringType(), required=False),
        ]
    )


def news_schema() -> Schema:
    return _schema_with_extras(
        [
            NestedField(100, "headline", StringType(), required=True),
            NestedField(101, "summary", StringType(), required=False),
            NestedField(102, "url_ref", StringType(), required=False),
            NestedField(103, "topics_json", StringType(), required=False),
            NestedField(104, "language", StringType(), required=False),
        ]
    )
