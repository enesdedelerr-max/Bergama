"""Deterministic AI Decision Engine foundation evaluation."""

from __future__ import annotations

from datetime import datetime

from app.ai_decision_engine.acceptance import evaluate_governed_acceptance
from app.ai_decision_engine.admit import coerce_evaluation_request
from app.ai_decision_engine.errors import AdeUnauthorizedInputError, AdeValidationError
from app.ai_decision_engine.models import AdeConfig, AdeEvaluationRequest, AdeResult
from app.human_review import HumanReviewOutput


def evaluate_ade(request: AdeEvaluationRequest | object) -> AdeResult:
    """Evaluate ADE under Policy Version v1 from authorized HR public evidence only."""
    validated = coerce_evaluation_request(request)
    return evaluate_governed_acceptance(validated)


def evaluate_ade_from_parts(
    *,
    human_review: HumanReviewOutput | None,
    as_of: datetime,
    config: AdeConfig | object | None = None,
) -> AdeResult:
    """Convenience entrypoint that coerces ADE parts into AdeEvaluationRequest."""
    if not isinstance(as_of, datetime):
        raise AdeValidationError(detail="invalid_as_of")
    if human_review is not None and not isinstance(human_review, HumanReviewOutput):
        raise AdeUnauthorizedInputError(detail="unauthorized_non_human_review_input")
    resolved_config = (
        AdeConfig()
        if config is None
        else (config if isinstance(config, AdeConfig) else AdeConfig.model_validate(config))
    )
    request = AdeEvaluationRequest(
        human_review=human_review,
        as_of=as_of,
        config=resolved_config,
    )
    return evaluate_ade(request)
