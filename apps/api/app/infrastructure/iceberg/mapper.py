"""Canonical event → Iceberg row mapping (#307)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.events.envelope import EventEnvelope
from app.infrastructure.iceberg.errors import (
    IcebergCanonicalError,
    IcebergDecimalError,
    IcebergEnvelopeError,
    IcebergMappingError,
    IcebergSchemaVersionError,
)
from app.infrastructure.iceberg.schemas import (
    DECIMAL_PRECISION,
    DECIMAL_SCALE,
    SUPPORTED_SCHEMA_VERSIONS,
)
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.events.bar import BarEvent
from app.market_data.events.filing import FilingEvent
from app.market_data.events.fundamental import FundamentalEvent
from app.market_data.events.macro import MacroEvent
from app.market_data.events.news import NewsEvent
from app.market_data.events.quote import QuoteEvent
from app.market_data.events.reference import ReferenceDataEvent
from app.market_data.events.trade import TradeEvent
from app.market_data.keys import build_deduplication_key, build_idempotency_key
from app.market_data.money import require_finite_decimal
from app.market_data.serialization import CANONICAL_MARKET_SCHEMA_VERSION, market_event_from_payload

_MAX_METADATA_JSON_BYTES = 8_192


def reconstruct_canonical_event(envelope: EventEnvelope) -> CanonicalMarketEvent:
    """Validate envelope schema version and rebuild CanonicalMarketEvent."""
    if not envelope.event_type.startswith("market."):
        msg = "envelope event_type is not a market-data event"
        raise IcebergEnvelopeError(msg)
    version = envelope.schema_version.strip()
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        msg = f"unsupported schema_version {envelope.schema_version!r}"
        raise IcebergSchemaVersionError(msg)
    if version != CANONICAL_MARKET_SCHEMA_VERSION:
        msg = f"unsupported schema_version {envelope.schema_version!r}"
        raise IcebergSchemaVersionError(msg)
    try:
        return market_event_from_payload(envelope.payload)
    except (ValueError, TypeError) as exc:
        msg = "canonical market event reconstruction failed"
        raise IcebergCanonicalError(msg) from exc


def map_envelope_to_row(envelope: EventEnvelope, event: CanonicalMarketEvent) -> dict[str, Any]:
    """Map envelope + canonical event to a flat Iceberg row dict."""
    try:
        row = _common_row(envelope, event)
        match event:
            case QuoteEvent():
                row.update(
                    {
                        "bid_price": to_iceberg_decimal(event.bid_price),
                        "bid_size": to_iceberg_decimal(event.bid_size),
                        "ask_price": to_iceberg_decimal(event.ask_price),
                        "ask_size": to_iceberg_decimal(event.ask_size),
                    }
                )
            case TradeEvent():
                row.update(
                    {
                        "price": to_iceberg_decimal(event.price),
                        "size": to_iceberg_decimal(event.size),
                        "trade_id": event.trade_id,
                    }
                )
            case BarEvent():
                row.update(
                    {
                        "window_start": _ts(event.window_start),
                        "window_end": _ts(event.window_end),
                        "close_time": _ts(event.close_time),
                        "open": to_iceberg_decimal(event.open),
                        "high": to_iceberg_decimal(event.high),
                        "low": to_iceberg_decimal(event.low),
                        "close": to_iceberg_decimal(event.close),
                        "volume": to_iceberg_decimal(event.volume),
                        "vwap": to_iceberg_decimal(event.vwap) if event.vwap is not None else None,
                        "trade_count": event.trade_count,
                    }
                )
            case ReferenceDataEvent():
                row.update(
                    {
                        "name": event.name,
                        "reference_attributes_json": _safe_json(event.attributes) or None,
                    }
                )
            case FundamentalEvent():
                row.update(
                    {
                        "metric_code": event.metric_code,
                        "period": event.period,
                        "value": to_iceberg_decimal(event.value),
                        "unit": event.unit,
                    }
                )
            case MacroEvent():
                row.update(
                    {
                        "series_id": event.series_id,
                        "value": to_iceberg_decimal(event.value),
                        "frequency": event.frequency,
                        "provider_units": event.unit,
                    }
                )
            case FilingEvent():
                row.update(
                    {
                        "form_type": event.form_type,
                        "accession_number": event.accession_number,
                        "filing_date": None,
                        "report_date": None,
                        "filing_url": event.document_ref,
                        "is_amendment": False,
                        "title": event.title,
                    }
                )
            case NewsEvent():
                row.update(
                    {
                        "headline": event.headline,
                        "summary": event.summary,
                        "url_ref": event.url_ref,
                        "topics_json": _safe_json(list(event.topics)) or None,
                        "language": event.language,
                    }
                )
            case _:
                msg = "unsupported canonical event type for Iceberg mapping"
                raise IcebergMappingError(msg)
        return row
    except (IcebergDecimalError, IcebergMappingError):
        raise
    except Exception as exc:
        msg = "Iceberg row mapping failed"
        raise IcebergMappingError(msg) from exc


def estimate_row_bytes(row: dict[str, Any]) -> int:
    """Conservative UTF-8 JSON size estimate for batch byte bounds."""
    try:
        encoded = json.dumps(row, default=str, separators=(",", ":"), sort_keys=True)
        return len(encoded.encode("utf-8"))
    except (TypeError, ValueError):
        return 1024


def to_iceberg_decimal(value: Decimal | int | str) -> Decimal:
    """Parse finite Decimal and enforce decimal(38,18). Reject binary floats."""
    if isinstance(value, float):
        msg = "binary float values are not allowed"
        raise IcebergDecimalError(msg)
    try:
        decimal_value = require_finite_decimal(value, field_name="decimal")
    except ValueError as exc:
        raise IcebergDecimalError(str(exc)) from exc
    _sign, digits, exponent = decimal_value.as_tuple()
    if isinstance(exponent, str):
        msg = "decimal must be finite"
        raise IcebergDecimalError(msg)
    if exponent < -DECIMAL_SCALE:
        msg = "decimal exceeds configured scale"
        raise IcebergDecimalError(msg)
    if len(digits) > DECIMAL_PRECISION:
        msg = "decimal exceeds configured precision"
        raise IcebergDecimalError(msg)
    try:
        return decimal_value.quantize(Decimal(1).scaleb(-DECIMAL_SCALE))
    except InvalidOperation as exc:
        msg = "decimal exceeds configured scale"
        raise IcebergDecimalError(msg) from exc


def _common_row(envelope: EventEnvelope, event: CanonicalMarketEvent) -> dict[str, Any]:
    idem = build_idempotency_key(event)
    if envelope.idempotency_key != idem:
        msg = "envelope idempotency_key does not match canonical event"
        raise IcebergMappingError(msg)
    metadata_json = _safe_json(dict(event.metadata))
    if metadata_json is not None and len(metadata_json.encode("utf-8")) > _MAX_METADATA_JSON_BYTES:
        msg = "metadata_json exceeds bound"
        raise IcebergMappingError(msg)
    return {
        "event_id": str(envelope.event_id),
        "event_type": envelope.event_type,
        "schema_version": envelope.schema_version,
        "source_system": envelope.source_system,
        "occurred_at": _ts(event.occurred_at),
        "ingested_at": _ts(event.ingested_at),
        "effective_at": _ts(event.effective_at),
        "known_at": _ts(event.known_at),
        "instrument_key": event.instrument.instrument_key,
        "asset_class": event.instrument.asset_class.value,
        "local_symbol": event.instrument.local_symbol,
        "idempotency_key": idem,
        "deduplication_key": build_deduplication_key(event),
        "source_provider": event.source.provider,
        "source_event_id": event.source.source_event_id,
        "correlation_id": envelope.correlation_id,
        "is_late": event.quality.is_late,
        "is_revision": event.quality.is_revision,
        "is_stale": event.quality.is_stale,
        "is_estimated": event.quality.is_estimated,
        "is_incomplete": event.quality.is_incomplete,
        "revision_of_event_id": event.quality.revision_of_event_id,
        "late_arrival_lag_ms": event.quality.late_arrival_lag_ms,
        "adjustment_state": event.adjustment_state.value,
        "currency": event.currency,
        "venue": event.venue,
        "metadata_json": metadata_json,
    }


def _ts(value: datetime) -> datetime:
    if value.tzinfo is None:
        msg = "timestamp must be timezone-aware UTC"
        raise IcebergMappingError(msg)
    return value.astimezone(UTC)


def _safe_json(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, (dict, list)) and len(value) == 0:
        return None
    try:
        return json.dumps(value, separators=(",", ":"), sort_keys=True, ensure_ascii=True)
    except (TypeError, ValueError) as exc:
        msg = "json serialization failed for bounded field"
        raise IcebergMappingError(msg) from exc
