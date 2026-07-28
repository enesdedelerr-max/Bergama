"""Premarket Intelligence bounded context — Sprint 7 Watchlist Engine foundation."""

from __future__ import annotations

from app.premarket.errors import (
    PremarketDisabledError,
    PremarketError,
    WatchlistDuplicateInstrumentError,
    WatchlistError,
    WatchlistUnsupportedCandidateError,
    WatchlistValidationError,
)
from app.premarket.settings import PremarketSettings
from app.premarket.watchlist import (
    ORDERING_POLICY_RULE_PRIORITY_ASC_INSTRUMENT_KEY_ASC,
    Watchlist,
    WatchlistCandidate,
    WatchlistConfig,
    WatchlistEntry,
    WatchlistGenerationRequest,
    WatchlistInclusionRule,
    WatchlistProvenance,
    generate_watchlist,
    generate_watchlist_from_parts,
    normalize_candidate,
    normalize_candidates,
    watchlist_sort_key,
)

__all__ = [
    "ORDERING_POLICY_RULE_PRIORITY_ASC_INSTRUMENT_KEY_ASC",
    "PremarketDisabledError",
    "PremarketError",
    "PremarketSettings",
    "Watchlist",
    "WatchlistCandidate",
    "WatchlistConfig",
    "WatchlistDuplicateInstrumentError",
    "WatchlistEntry",
    "WatchlistError",
    "WatchlistGenerationRequest",
    "WatchlistInclusionRule",
    "WatchlistProvenance",
    "WatchlistUnsupportedCandidateError",
    "WatchlistValidationError",
    "generate_watchlist",
    "generate_watchlist_from_parts",
    "normalize_candidate",
    "normalize_candidates",
    "watchlist_sort_key",
]
