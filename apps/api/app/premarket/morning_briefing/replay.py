"""Replay helpers for Morning Briefing."""

from __future__ import annotations

from app.premarket.errors import BriefingInvariantError
from app.premarket.morning_briefing.engine import assemble_briefing
from app.premarket.morning_briefing.models import BriefingCollection, BriefingRequest
from app.premarket.settings import PremarketSettings


def reassemble(
    request: BriefingRequest,
    *,
    settings: PremarketSettings | None = None,
) -> BriefingCollection:
    """Re-execute Morning Briefing assembly for pinned input (test/helper path)."""
    return assemble_briefing(request, settings=settings)


def assert_replay_equal(
    first: BriefingCollection,
    second: BriefingCollection,
) -> None:
    """Fail closed when two Morning Briefing outputs are not replay-equal."""
    if first.model_dump(mode="python") != second.model_dump(mode="python"):
        raise BriefingInvariantError(detail="replay_inequality")
