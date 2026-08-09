"""Replay helpers for Dashboard."""

from __future__ import annotations

from app.dashboard.engine import assemble_dashboard
from app.dashboard.errors import DashboardReplayInequalityError
from app.dashboard.models import DashboardPresentationOutput, DashboardRequest


def reassemble(request: DashboardRequest) -> DashboardPresentationOutput:
    """Re-execute Dashboard presentation for pinned input (test/helper path)."""
    return assemble_dashboard(request)


def assert_replay_equal(
    first: DashboardPresentationOutput,
    second: DashboardPresentationOutput,
) -> None:
    """Fail closed when two Dashboard outputs are not replay-equal."""
    if first.model_dump(mode="python") != second.model_dump(mode="python"):
        raise DashboardReplayInequalityError(detail="replay_inequality")
