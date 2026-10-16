"""Replay helpers for Premarket Analyst projection."""

from __future__ import annotations

from app.premarket_analyst.engine import project_analyst
from app.premarket_analyst.errors import PremarketAnalystReplayInequalityError
from app.premarket_analyst.models import AnalystProjectionRequest, PremarketAnalystArtifact


def reproject(request: AnalystProjectionRequest) -> PremarketAnalystArtifact:
    """Re-execute projection for pinned input (test/helper path)."""
    return project_analyst(request)


def assert_replay_equal(
    first: PremarketAnalystArtifact,
    second: PremarketAnalystArtifact,
) -> None:
    """Fail closed when two analyst artifacts are not replay-equal."""
    if first.model_dump(mode="python") != second.model_dump(mode="python"):
        raise PremarketAnalystReplayInequalityError(detail="replay_inequality")
