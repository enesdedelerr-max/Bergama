"""Deterministic Premarket Scoring engine."""

from __future__ import annotations

from datetime import datetime

from app.premarket.catalyst.models import CatalystCollection
from app.premarket.errors import PremarketDisabledError, ScoreValidationError
from app.premarket.gap.models import GapCollection
from app.premarket.scoring.models import ScoreCollection, ScoreConfig, ScoreRequest
from app.premarket.scoring.pipeline import run_scoring_pipeline
from app.premarket.scoring.resolve_policy import resolve_policy
from app.premarket.scoring.validate_input import validate_score_request
from app.premarket.settings import PremarketSettings
from app.premarket.watchlist.models import Watchlist


def scan_scores(
    request: ScoreRequest | object,
    *,
    settings: PremarketSettings | None = None,
) -> ScoreCollection:
    """Score Watchlist instruments under Policy Version v1.

    When ``settings`` is provided, enablement must be true (fail-closed).
    When ``settings`` is omitted, scoring runs for direct unit use.
    """
    if settings is not None and not settings.enabled:
        raise PremarketDisabledError(detail="premarket_disabled")

    validated_model = _coerce_request(request)
    validated = validate_score_request(validated_model, settings=None)
    bound = resolve_policy(validated.config)
    return run_scoring_pipeline(validated, bound)


def scan_scores_from_parts(
    *,
    watchlist: Watchlist | object,
    as_of: datetime,
    config: ScoreConfig | object | None = None,
    catalysts: CatalystCollection | object | None = None,
    gaps: GapCollection | object | None = None,
    settings: PremarketSettings | None = None,
) -> ScoreCollection:
    """Convenience entrypoint that coerces scoring parts into ScoreRequest."""
    if not isinstance(as_of, datetime):
        raise ScoreValidationError(detail="invalid_as_of")
    resolved_watchlist = (
        watchlist if isinstance(watchlist, Watchlist) else Watchlist.model_validate(watchlist)
    )
    resolved_catalysts: CatalystCollection | None
    if catalysts is None:
        resolved_catalysts = None
    elif isinstance(catalysts, CatalystCollection):
        resolved_catalysts = catalysts
    else:
        resolved_catalysts = CatalystCollection.model_validate(catalysts)

    resolved_gaps: GapCollection | None
    if gaps is None:
        resolved_gaps = None
    elif isinstance(gaps, GapCollection):
        resolved_gaps = gaps
    else:
        resolved_gaps = GapCollection.model_validate(gaps)

    request = ScoreRequest(
        watchlist=resolved_watchlist,
        as_of=as_of,
        config=(
            ScoreConfig()
            if config is None
            else (config if isinstance(config, ScoreConfig) else ScoreConfig.model_validate(config))
        ),
        catalysts=resolved_catalysts,
        gaps=resolved_gaps,
    )
    return scan_scores(request, settings=settings)


def _coerce_request(request: object) -> ScoreRequest:
    if isinstance(request, ScoreRequest):
        return request
    try:
        return ScoreRequest.model_validate(request)
    except Exception as exc:
        raise ScoreValidationError(detail=f"invalid_request:{exc}") from exc
