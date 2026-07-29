"""Deterministic gap record identity."""

from __future__ import annotations

from decimal import Decimal

from app.market_data.money import canonical_decimal_str
from app.strategy.keys import strategy_sha256

_IDENTITY_SCHEMA = "premarket.gap.record.v1"


def build_gap_record_id(
    *,
    instrument_key: str,
    previous_session_close: Decimal,
    current_session_open: Decimal,
    gap_percent: Decimal,
    as_of: object,
    selection_policy_id: str,
    previous_bar_close_time: object,
    current_bar_close_time: object,
    previous_bar_source_event_id: str | None,
    current_bar_source_event_id: str | None,
) -> str:
    """Return a stable sha256 hex identity for a gap observation."""
    return strategy_sha256(
        {
            "schema": _IDENTITY_SCHEMA,
            "instrument_key": instrument_key,
            "previous_session_close": canonical_decimal_str(previous_session_close),
            "current_session_open": canonical_decimal_str(current_session_open),
            "gap_percent": canonical_decimal_str(gap_percent),
            "as_of": as_of,
            "selection_policy_id": selection_policy_id,
            "previous_bar_close_time": previous_bar_close_time,
            "current_bar_close_time": current_bar_close_time,
            "previous_bar_source_event_id": previous_bar_source_event_id or "",
            "current_bar_source_event_id": current_bar_source_event_id or "",
        }
    )
