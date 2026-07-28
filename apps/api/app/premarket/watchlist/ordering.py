"""Deterministic watchlist ordering policy."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.premarket.watchlist.models import WatchlistInclusionRule

ORDERING_POLICY_RULE_PRIORITY_ASC_INSTRUMENT_KEY_ASC = "rule_priority_asc_instrument_key_asc"


def watchlist_sort_key(
    *,
    rule: WatchlistInclusionRule,
    instrument_key: str,
) -> tuple[int, str]:
    """Stable total order: (rule_priority ASC, instrument_key ASC)."""
    return (rule.rule_priority, instrument_key)
