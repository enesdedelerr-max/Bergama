"""Replay / PIT helpers for AI Decision Engine foundation."""

from __future__ import annotations

from app.ai_decision_engine.engine import evaluate_ade
from app.ai_decision_engine.errors import AdeReplayInequalityError
from app.ai_decision_engine.models import AdeEvaluationRequest, AdeResult


def reevaluate(request: AdeEvaluationRequest) -> AdeResult:
    """Re-execute ADE for pinned authorized evidence + Policy context + as_of."""
    return evaluate_ade(request)


def assert_replay_equal(first: AdeResult, second: AdeResult) -> None:
    """Fail closed when two ADE results are not replay-equal."""
    if first.model_dump(mode="python") != second.model_dump(mode="python"):
        raise AdeReplayInequalityError(detail="replay_inequality")
