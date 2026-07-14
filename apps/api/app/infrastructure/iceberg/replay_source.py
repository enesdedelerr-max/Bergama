"""Iceberg-backed ReplaySource (#308).

Primary MVP source. Reads the eight approved tables only. Reconstructs
CanonicalMarketEvent from stored columns with the approved lossy policy for
missing ``symbol_effective_from``. Does not invent Kafka provenance.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from pyiceberg.catalog import Catalog
from pyiceberg.expressions import (
    And,
    EqualTo,
    GreaterThanOrEqual,
    In,
    LessThan,
    Reference,
)

from app.core.iceberg_writer_settings import IcebergWriterSettings
from app.infrastructure.iceberg.catalog import load_required_table
from app.infrastructure.iceberg.errors import IcebergCatalogError
from app.infrastructure.iceberg.schemas import SUPPORTED_SCHEMA_VERSIONS
from app.market_data.enums import AdjustmentState, AssetClass, MarketEventType
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.events.bar import BarEvent
from app.market_data.events.filing import FilingEvent
from app.market_data.events.fundamental import FundamentalEvent
from app.market_data.events.macro import MacroEvent
from app.market_data.events.news import NewsEvent
from app.market_data.events.quote import QuoteEvent
from app.market_data.events.reference import ReferenceDataEvent
from app.market_data.events.trade import TradeEvent
from app.market_data.identity import InstrumentId
from app.market_data.keys import build_idempotency_key
from app.market_data.quality import DataQualityFlags
from app.market_data.replay.errors import (
    ReplayIdempotencyMismatchError,
    ReplayReconstructionError,
    ReplaySourceReadError,
    ReplayUnsupportedSchemaError,
)
from app.market_data.replay.models import EVENT_TYPE_TO_TABLE, ReplayRecord, ReplayRequest
from app.market_data.replay.ordering import sort_replay_records
from app.market_data.source import SourceReference
from app.market_data.timing import require_utc_aware

_TABLE_TO_EVENT_TYPE: dict[str, str] = {v: k for k, v in EVENT_TYPE_TO_TABLE.items()}

_COMMON_REQUIRED = frozenset(
    {
        "event_id",
        "event_type",
        "schema_version",
        "source_system",
        "occurred_at",
        "ingested_at",
        "effective_at",
        "known_at",
        "instrument_key",
        "asset_class",
        "idempotency_key",
        "deduplication_key",
        "source_provider",
        "is_late",
        "is_revision",
        "is_stale",
        "is_estimated",
        "is_incomplete",
        "adjustment_state",
    }
)


class IcebergReplaySource:
    """Bounded Iceberg table reader for the eight canonical market-data tables."""

    def __init__(
        self,
        catalog: Catalog,
        settings: IcebergWriterSettings,
        *,
        owns_catalog: bool = False,
    ) -> None:
        self._catalog = catalog
        self._settings = settings
        self._owns_catalog = owns_catalog
        self._closed = False

    async def fetch(self, request: ReplayRequest) -> Sequence[ReplayRecord]:
        if self._closed:
            raise ReplaySourceReadError(detail="replay source is closed")
        records: list[ReplayRecord] = []
        # Safety bound: refuse scans that would inflate far beyond max_records
        # before deterministic truncation (no unbounded lake read).
        raw_cap = max(request.max_records * 20, request.max_records)
        try:
            for table_base in request.resolved_table_bases():
                table_records = self._scan_table(
                    table_base=table_base,
                    request=request,
                    limit=raw_cap - len(records) + 1,
                )
                records.extend(table_records)
                if len(records) > raw_cap:
                    raise ReplaySourceReadError(
                        detail="source result exceeds bounded scan safety cap"
                    )
        except (
            ReplayUnsupportedSchemaError,
            ReplayReconstructionError,
            ReplayIdempotencyMismatchError,
            ReplaySourceReadError,
        ):
            raise
        except Exception as exc:
            raise ReplaySourceReadError(detail="iceberg scan failed") from exc

        ordered = sort_replay_records(records)
        return ordered[: request.max_records]

    async def aclose(self) -> None:
        self._closed = True

    def _scan_table(
        self,
        *,
        table_base: str,
        request: ReplayRequest,
        limit: int,
    ) -> list[ReplayRecord]:
        table_name = (
            f"{self._settings.table_prefix}{table_base}"
            if self._settings.table_prefix
            else table_base
        )
        try:
            table = load_required_table(
                self._catalog,
                namespace=self._settings.namespace,
                table_name=table_name,
            )
        except IcebergCatalogError as exc:
            raise ReplaySourceReadError(detail=f"table load failed for {table_base}") from exc

        expected_event_type = _TABLE_TO_EVENT_TYPE[table_base]
        start = request.start_time.astimezone(UTC)
        end = request.end_time.astimezone(UTC)
        predicates: list[Any] = [
            _expr(GreaterThanOrEqual, "occurred_at", start),
            _expr(LessThan, "occurred_at", end),
            _expr(EqualTo, "event_type", expected_event_type),
        ]
        if request.instrument_keys:
            predicates.append(_expr_in("instrument_key", set(request.instrument_keys)))
        if request.source_providers:
            predicates.append(_expr_in("source_provider", set(request.source_providers)))

        row_filter = predicates[0]
        for pred in predicates[1:]:
            row_filter = And(row_filter, pred)

        try:
            arrow = table.scan(row_filter=row_filter).to_arrow()
        except Exception as exc:
            raise ReplaySourceReadError(detail=f"scan failed for {table_base}") from exc

        out: list[ReplayRecord] = []
        for i in range(len(arrow)):
            if len(out) >= limit:
                break
            row = {name: arrow[name][i].as_py() for name in arrow.column_names}
            event, synthetic = reconstruct_row_to_canonical(row, table_base=table_base)
            idem = build_idempotency_key(event)
            stored_idem = str(row["idempotency_key"])
            if idem != stored_idem:
                raise ReplayIdempotencyMismatchError(
                    detail=f"idempotency mismatch for {table_base}"
                )
            out.append(
                ReplayRecord(
                    occurred_at=require_utc_aware(event.occurred_at, field_name="occurred_at"),
                    event_type=str(row["event_type"]),
                    instrument_key=event.instrument.instrument_key,
                    idempotency_key=stored_idem,
                    table_base=table_base,
                    event=event,
                    synthetic_symbol_effective_from=synthetic,
                )
            )
        return out


def reconstruct_row_to_canonical(
    row: dict[str, Any],
    *,
    table_base: str,
) -> tuple[CanonicalMarketEvent, bool]:
    """Lossy Iceberg row → CanonicalMarketEvent.

    Never claimed as lossless. Missing ``symbol_effective_from`` derives from
    ``effective_at`` then ``occurred_at`` (synthetic reconstruction).
    """
    missing = [name for name in _COMMON_REQUIRED if name not in row or row[name] is None]
    if missing:
        raise ReplayReconstructionError(detail=f"missing required columns: {sorted(missing)[:8]}")

    schema_version = str(row["schema_version"]).strip()
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ReplayUnsupportedSchemaError(detail=f"unsupported schema_version {schema_version!r}")

    event_type_raw = str(row["event_type"]).strip()
    expected = _TABLE_TO_EVENT_TYPE.get(table_base)
    if expected is None or event_type_raw != expected:
        raise ReplayReconstructionError(detail="event_type/table mismatch")

    occurred_at = _require_ts(row["occurred_at"], "occurred_at")
    effective_at = _require_ts(row["effective_at"], "effective_at")
    known_at = _require_ts(row["known_at"], "known_at")
    ingested_at = _require_ts(row["ingested_at"], "ingested_at")

    symbol_from_raw = row.get("symbol_effective_from")
    synthetic = False
    if symbol_from_raw is not None:
        symbol_effective_from = _require_ts(symbol_from_raw, "symbol_effective_from")
    else:
        synthetic = True
        symbol_effective_from = effective_at if effective_at is not None else occurred_at

    try:
        instrument = InstrumentId(
            instrument_key=str(row["instrument_key"]),
            asset_class=AssetClass(str(row["asset_class"])),
            local_symbol=row.get("local_symbol"),
            symbol_effective_from=symbol_effective_from,
            symbol_effective_to=_optional_ts(row.get("symbol_effective_to")),
        )
        source = SourceReference(
            provider=str(row["source_provider"]),
            source_event_id=row.get("source_event_id"),
            # source_symbol / extras / payload_ref intentionally omitted — not stored.
        )
        quality = DataQualityFlags(
            is_late=bool(row["is_late"]),
            is_revision=bool(row["is_revision"]),
            is_stale=bool(row["is_stale"]),
            is_estimated=bool(row["is_estimated"]),
            is_incomplete=bool(row["is_incomplete"]),
            revision_of_event_id=row.get("revision_of_event_id"),
            late_arrival_lag_ms=row.get("late_arrival_lag_ms"),
        )
        metadata = _parse_metadata(row.get("metadata_json"))
        common: dict[str, Any] = {
            "schema_version": schema_version,
            "instrument": instrument,
            "source": source,
            "quality": quality,
            "adjustment_state": AdjustmentState(str(row["adjustment_state"])),
            "occurred_at": occurred_at,
            "effective_at": effective_at,
            "known_at": known_at,
            "ingested_at": ingested_at,
            "currency": row.get("currency"),
            "venue": row.get("venue"),
            "metadata": metadata,
        }
        event = _build_typed_event(table_base, common, row)
    except (ReplayReconstructionError, ReplayUnsupportedSchemaError):
        raise
    except Exception as exc:
        raise ReplayReconstructionError(detail="canonical reconstruction failed") from exc

    return event, synthetic


def _build_typed_event(
    table_base: str,
    common: dict[str, Any],
    row: dict[str, Any],
) -> CanonicalMarketEvent:
    match table_base:
        case "market_quotes":
            return QuoteEvent.model_validate(
                {
                    **common,
                    "event_type": MarketEventType.QUOTE,
                    "bid_price": _decimal(row, "bid_price"),
                    "bid_size": _decimal(row, "bid_size"),
                    "ask_price": _decimal(row, "ask_price"),
                    "ask_size": _decimal(row, "ask_size"),
                }
            )
        case "market_trades":
            return TradeEvent.model_validate(
                {
                    **common,
                    "event_type": MarketEventType.TRADE,
                    "price": _decimal(row, "price"),
                    "size": _decimal(row, "size"),
                    "trade_id": row.get("trade_id"),
                    # aggressor_side not stored — remain omitted
                }
            )
        case "market_bars":
            return BarEvent.model_validate(
                {
                    **common,
                    "event_type": MarketEventType.BAR,
                    "window_start": _require_ts(row["window_start"], "window_start"),
                    "window_end": _require_ts(row["window_end"], "window_end"),
                    "close_time": _require_ts(row["close_time"], "close_time"),
                    "open": _decimal(row, "open"),
                    "high": _decimal(row, "high"),
                    "low": _decimal(row, "low"),
                    "close": _decimal(row, "close"),
                    "volume": _decimal(row, "volume"),
                    "vwap": _optional_decimal(row.get("vwap")),
                    "trade_count": row.get("trade_count"),
                }
            )
        case "market_reference_data":
            attrs = _parse_str_dict(row.get("reference_attributes_json"))
            return ReferenceDataEvent.model_validate(
                {
                    **common,
                    "event_type": MarketEventType.REFERENCE_DATA,
                    "name": row.get("name"),
                    "attributes": attrs,
                    # exchange_mic/isin/cusip/status not stored as columns
                }
            )
        case "market_fundamentals":
            return FundamentalEvent.model_validate(
                {
                    **common,
                    "event_type": MarketEventType.FUNDAMENTAL,
                    "metric_code": row["metric_code"],
                    "period": row["period"],
                    "value": _decimal(row, "value"),
                    "unit": row.get("unit"),
                }
            )
        case "market_macro":
            return MacroEvent.model_validate(
                {
                    **common,
                    "event_type": MarketEventType.MACRO,
                    "series_id": row["series_id"],
                    "value": _decimal(row, "value"),
                    "unit": row.get("provider_units"),
                    "frequency": row.get("frequency"),
                }
            )
        case "market_filings":
            return FilingEvent.model_validate(
                {
                    **common,
                    "event_type": MarketEventType.FILING,
                    "form_type": row["form_type"],
                    "accession_number": row["accession_number"],
                    "title": row.get("title"),
                    "document_ref": row.get("filing_url"),
                }
            )
        case "market_news":
            topics = _parse_topics(row.get("topics_json"))
            return NewsEvent.model_validate(
                {
                    **common,
                    "event_type": MarketEventType.NEWS,
                    "headline": row["headline"],
                    "summary": row.get("summary"),
                    "url_ref": row.get("url_ref"),
                    "language": row.get("language"),
                    "topics": topics,
                }
            )
        case _:
            raise ReplayReconstructionError(detail=f"unknown table_base {table_base!r}")


def _expr(factory: Any, field_name: str, value: object) -> Any:
    """Build a comparison expression; stubs for pyiceberg are incomplete."""
    return factory(Reference(field_name), value)


def _expr_in(field_name: str, values: set[str]) -> Any:
    factory: Any = In
    return factory(Reference(field_name), values)


def _require_ts(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise ReplayReconstructionError(detail=f"{field_name} must be timestamptz")
    return require_utc_aware(value, field_name=field_name)


def _optional_ts(value: object) -> datetime | None:
    if value is None:
        return None
    return _require_ts(value, "optional_ts")


def _decimal(row: dict[str, Any], name: str) -> Decimal:
    value = row.get(name)
    if value is None:
        raise ReplayReconstructionError(detail=f"missing decimal column {name}")
    if isinstance(value, float):
        raise ReplayReconstructionError(detail=f"binary float not allowed for {name}")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, float):
        raise ReplayReconstructionError(detail="binary float not allowed")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _parse_metadata(raw: object) -> dict[str, str]:
    if raw is None or raw == "":
        return {}
    if not isinstance(raw, str):
        raise ReplayReconstructionError(detail="metadata_json must be string")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ReplayReconstructionError(detail="metadata_json decode failed") from exc
    if not isinstance(parsed, dict):
        raise ReplayReconstructionError(detail="metadata_json must be object")
    out: dict[str, str] = {}
    for key, value in parsed.items():
        out[str(key)] = str(value)
    return out


def _parse_str_dict(raw: object) -> dict[str, str]:
    if raw is None or raw == "":
        return {}
    if not isinstance(raw, str):
        raise ReplayReconstructionError(detail="json object field must be string")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ReplayReconstructionError(detail="json object decode failed") from exc
    if not isinstance(parsed, dict):
        raise ReplayReconstructionError(detail="expected json object")
    return {str(k): str(v) for k, v in parsed.items()}


def _parse_topics(raw: object) -> tuple[str, ...]:
    if raw is None or raw == "":
        return ()
    if not isinstance(raw, str):
        raise ReplayReconstructionError(detail="topics_json must be string")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ReplayReconstructionError(detail="topics_json decode failed") from exc
    if not isinstance(parsed, list):
        raise ReplayReconstructionError(detail="topics_json must be list")
    return tuple(str(item) for item in parsed)
