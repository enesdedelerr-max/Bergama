"""Input Validation Layer for Premarket Scoring."""

from __future__ import annotations

from app.premarket.errors import (
    PremarketDisabledError,
    ScoreConflictError,
    ScoreValidationError,
)
from app.premarket.scoring.canonical import canonicalize_catalyst_collection
from app.premarket.scoring.models import ScoreRequest
from app.premarket.scoring.ports import ValidatedScoreRequest
from app.premarket.settings import PremarketSettings
from app.premarket.watchlist.models import Watchlist


def validate_score_request(
    request: ScoreRequest,
    *,
    settings: PremarketSettings | None = None,
) -> ValidatedScoreRequest:
    """Admit only Decision #3 / Policy Version v1-legal requests.

    Fail-closed when Premarket settings are supplied and disabled.
    """
    if settings is not None and not settings.enabled:
        raise PremarketDisabledError(detail="premarket_disabled")

    _assert_common_pit_context(request)
    _assert_watchlist_ranks(request.watchlist)

    catalysts = (
        None if request.catalysts is None else canonicalize_catalyst_collection(request.catalysts)
    )

    return ValidatedScoreRequest(
        watchlist=request.watchlist,
        as_of=request.as_of,
        config=request.config,
        catalysts=catalysts,
        gaps=request.gaps,
    )


def _assert_common_pit_context(request: ScoreRequest) -> None:
    """Reject cross-PIT collection mixing under a single scoring ``as_of``."""
    if request.gaps is not None and request.gaps.as_of != request.as_of:
        raise ScoreConflictError(
            detail=f"cross_pit_gaps:{request.gaps.as_of.isoformat()}:{request.as_of.isoformat()}"
        )
    if request.catalysts is not None and request.catalysts.as_of != request.as_of:
        raise ScoreConflictError(
            detail=(
                "cross_pit_catalysts:"
                f"{request.catalysts.as_of.isoformat()}:{request.as_of.isoformat()}"
            )
        )


def _assert_watchlist_ranks(watchlist: Watchlist) -> None:
    """Enforce Policy Version v1 Watchlist rank bounds before scoring math.

    Duplicate ranks across different instruments remain legal: Watchlist contracts
    do not require unique ranks, and Ordering Policy breaks remaining ties by
    ``instrument_key`` then ``score_record_id``.
    """
    universe_size = len(watchlist.entries)
    for entry in watchlist.entries:
        if entry.rank < 1:
            raise ScoreValidationError(detail=f"invalid_rank:{entry.instrument_key}:{entry.rank}")
        if universe_size > 0 and entry.rank > universe_size:
            raise ScoreValidationError(
                detail=(
                    f"rank_exceeds_universe:{entry.instrument_key}:{entry.rank}:{universe_size}"
                )
            )
