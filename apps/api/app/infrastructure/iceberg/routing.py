"""Explicit EventEnvelope.event_type → Iceberg table routing (#307)."""

from __future__ import annotations

from app.infrastructure.iceberg.errors import IcebergUnknownRouteError

# Immutable approved map — provider never selects the table.
_EVENT_TYPE_TO_TABLE: dict[str, str] = {
    "market.quote": "market_quotes",
    "market.trade": "market_trades",
    "market.bar": "market_bars",
    "market.reference_data": "market_reference_data",
    "market.fundamental": "market_fundamentals",
    "market.macro": "market_macro",
    "market.filing": "market_filings",
    "market.news": "market_news",
}


def approved_event_types() -> frozenset[str]:
    return frozenset(_EVENT_TYPE_TO_TABLE)


def table_for_event_type(event_type: str, *, table_prefix: str = "") -> str:
    """Return logical table name for an envelope event_type. Fail closed on unknown."""
    key = event_type.strip()
    base = _EVENT_TYPE_TO_TABLE.get(key)
    if base is None:
        msg = f"unknown market-data event type for Iceberg routing: {event_type!r}"
        raise IcebergUnknownRouteError(msg)
    prefix = table_prefix.strip()
    return f"{prefix}{base}" if prefix else base


def all_table_bases() -> tuple[str, ...]:
    """Stable alphabetical order of logical table base names."""
    return tuple(sorted(set(_EVENT_TYPE_TO_TABLE.values())))
