"""Replay helpers for Premarket Scoring."""

from __future__ import annotations

from app.premarket.errors import ScoreInvariantError
from app.premarket.scoring.engine import scan_scores
from app.premarket.scoring.models import ScoreCollection, ScoreRequest
from app.premarket.settings import PremarketSettings


def rescore(
    request: ScoreRequest,
    *,
    settings: PremarketSettings | None = None,
) -> ScoreCollection:
    """Re-execute scoring for pinned input (test/helper path)."""
    return scan_scores(request, settings=settings)


def assert_replay_equal(
    first: ScoreCollection,
    second: ScoreCollection,
) -> None:
    """Fail closed when two score collections are not replay-equal."""
    if first.model_dump(mode="python") != second.model_dump(mode="python"):
        raise ScoreInvariantError(detail="replay_inequality")
