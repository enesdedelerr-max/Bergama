"""Deterministic Morning Briefing engine."""

from __future__ import annotations

from datetime import datetime

from app.premarket.errors import BriefingValidationError
from app.premarket.morning_briefing.models import (
    BriefingCollection,
    BriefingConfig,
    BriefingRequest,
)
from app.premarket.morning_briefing.pipeline import run_briefing_pipeline
from app.premarket.morning_briefing.validate_input import validate_briefing_request
from app.premarket.scoring.models import ScoreCollection
from app.premarket.settings import PremarketSettings


def assemble_briefing(
    request: BriefingRequest | object,
    *,
    settings: PremarketSettings | None = None,
) -> BriefingCollection:
    """Assemble a Morning Briefing under Policy Version v1.

    When ``settings`` is provided, enablement must be true (fail-closed).
    When ``settings`` is omitted, assembly runs for direct unit use.
    """
    validated_model = _coerce_request(request)
    validated = validate_briefing_request(validated_model, settings=settings)
    return run_briefing_pipeline(validated)


def assemble_briefing_from_parts(
    *,
    scores: ScoreCollection | object,
    as_of: datetime,
    config: BriefingConfig | object | None = None,
    settings: PremarketSettings | None = None,
) -> BriefingCollection:
    """Convenience entrypoint that coerces briefing parts into BriefingRequest."""
    if not isinstance(as_of, datetime):
        raise BriefingValidationError(detail="invalid_as_of")
    resolved_scores = (
        scores if isinstance(scores, ScoreCollection) else ScoreCollection.model_validate(scores)
    )
    request = BriefingRequest(
        scores=resolved_scores,
        as_of=as_of,
        config=(
            BriefingConfig()
            if config is None
            else (
                config
                if isinstance(config, BriefingConfig)
                else BriefingConfig.model_validate(config)
            )
        ),
    )
    return assemble_briefing(request, settings=settings)


def _coerce_request(request: object) -> BriefingRequest:
    if isinstance(request, BriefingRequest):
        return request
    try:
        return BriefingRequest.model_validate(request)
    except Exception as exc:
        raise BriefingValidationError(detail=f"invalid_request:{exc}") from exc
