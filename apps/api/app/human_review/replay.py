"""Replay helpers for Human Review."""

from __future__ import annotations

from app.human_review.engine import assemble_human_review
from app.human_review.errors import HumanReviewReplayInequalityError
from app.human_review.models import HumanReviewOutput, HumanReviewRequest


def reassemble(request: HumanReviewRequest) -> HumanReviewOutput:
    """Re-execute Human Review for pinned input (test/helper path)."""
    return assemble_human_review(request)


def assert_replay_equal(
    first: HumanReviewOutput,
    second: HumanReviewOutput,
) -> None:
    """Fail closed when two Human Review outputs are not replay-equal."""
    if first.model_dump(mode="python") != second.model_dump(mode="python"):
        raise HumanReviewReplayInequalityError(detail="replay_inequality")
