"""Deterministic idempotency and deduplication key builders."""

from __future__ import annotations

from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.events.bar import BarEvent
from app.market_data.events.filing import FilingEvent
from app.market_data.events.fundamental import FundamentalEvent
from app.market_data.events.macro import MacroEvent
from app.market_data.events.news import NewsEvent
from app.market_data.events.quote import QuoteEvent
from app.market_data.events.reference import ReferenceDataEvent
from app.market_data.events.trade import TradeEvent
from app.market_data.money import canonical_decimal_str
from app.market_data.timing import require_utc_aware


def _ts(value: object) -> str:
    from datetime import datetime

    if not isinstance(value, datetime):
        msg = "timestamp required"
        raise TypeError(msg)
    return require_utc_aware(value, field_name="ts").isoformat().replace("+00:00", "Z")


def build_idempotency_key(event: CanonicalMarketEvent) -> str:
    """Stable key across replay for the same logical observation.

    Includes revision identity so a restatement does not silently overwrite.
    """
    parts = [
        "mkt",
        event.event_type.value,
        event.schema_version,
        event.instrument.instrument_key,
        _ts(event.occurred_at),
        event.source.provider,
        event.source.source_event_id or "",
        "rev" if event.quality.is_revision else "orig",
        event.quality.revision_of_event_id or "",
    ]
    return "|".join(parts)


def build_deduplication_key(event: CanonicalMarketEvent) -> str:
    """Deterministic key for near-term duplicate suppression.

    Prefer provider event IDs when present; otherwise use type-specific fingerprints.
    """
    base = [
        event.event_type.value,
        event.instrument.instrument_key,
        _ts(event.occurred_at),
        event.source.provider,
    ]
    if event.source.source_event_id:
        return "|".join([*base, "sid", event.source.source_event_id])

    match event:
        case TradeEvent():
            fingerprint = [
                "trade",
                event.trade_id or "",
                canonical_decimal_str(event.price),
                canonical_decimal_str(event.size),
                event.venue or "",
            ]
        case QuoteEvent():
            fingerprint = [
                "quote",
                canonical_decimal_str(event.bid_price),
                canonical_decimal_str(event.ask_price),
                canonical_decimal_str(event.bid_size),
                canonical_decimal_str(event.ask_size),
                event.venue or "",
            ]
        case BarEvent():
            fingerprint = [
                "bar",
                _ts(event.window_start),
                _ts(event.window_end),
                _ts(event.close_time),
                canonical_decimal_str(event.close),
                canonical_decimal_str(event.volume),
                event.adjustment_state.value,
            ]
        case ReferenceDataEvent():
            fingerprint = ["ref", event.isin or "", event.cusip or "", event.status or ""]
        case FundamentalEvent():
            fingerprint = [
                "fund",
                event.metric_code,
                event.period,
                canonical_decimal_str(event.value),
            ]
        case MacroEvent():
            fingerprint = ["macro", event.series_id, canonical_decimal_str(event.value)]
        case FilingEvent():
            fingerprint = ["filing", event.form_type, event.accession_number]
        case NewsEvent():
            fingerprint = ["news", event.headline[:128], event.url_ref or ""]
        case _:
            fingerprint = ["unknown"]
    return "|".join([*base, *fingerprint])
