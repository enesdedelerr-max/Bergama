"""Candidate and identity normalization for the Watchlist Engine."""

from __future__ import annotations

from typing import Any

from app.market_data.identity import InstrumentId
from app.premarket.errors import (
    WatchlistUnsupportedCandidateError,
    WatchlistValidationError,
)
from app.premarket.watchlist.models import WatchlistCandidate


def normalize_candidate(candidate: object) -> WatchlistCandidate:
    """Normalize a candidate into an immutable WatchlistCandidate.

    Accepted inputs:
    - ``WatchlistCandidate``
    - ``InstrumentId`` (uses ``instrument_key`` and effective-dated ``local_symbol``)

    All other types fail closed.
    """
    if isinstance(candidate, WatchlistCandidate):
        return candidate

    if isinstance(candidate, InstrumentId):
        key = candidate.instrument_key.strip()
        if not key:
            raise WatchlistValidationError(detail="invalid_instrument_key")
        symbol = candidate.local_symbol.strip() if candidate.local_symbol else None
        return WatchlistCandidate(
            instrument_key=key,
            local_symbol=symbol or None,
        )

    if isinstance(candidate, dict):
        try:
            return WatchlistCandidate.model_validate(candidate)
        except Exception as exc:
            raise WatchlistValidationError(detail=f"invalid_candidate:{exc}") from exc

    raise WatchlistUnsupportedCandidateError(
        detail=f"unsupported_candidate:{type(candidate).__name__}"
    )


def normalize_candidates(candidates: Any) -> tuple[WatchlistCandidate, ...]:
    """Normalize an ordered candidate sequence."""
    if candidates is None:
        raise WatchlistUnsupportedCandidateError(detail="unsupported_candidate:NoneType")
    if isinstance(candidates, (str, bytes)):
        raise WatchlistUnsupportedCandidateError(
            detail=f"unsupported_candidate:{type(candidates).__name__}"
        )
    try:
        iterator = list(candidates)
    except TypeError as exc:
        raise WatchlistUnsupportedCandidateError(
            detail=f"unsupported_candidate:{type(candidates).__name__}"
        ) from exc
    return tuple(normalize_candidate(item) for item in iterator)
