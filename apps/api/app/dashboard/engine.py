"""Deterministic Dashboard presentation engine."""

from __future__ import annotations

from datetime import datetime

from app.dashboard.errors import DashboardValidationError
from app.dashboard.models import (
    DashboardConfig,
    DashboardPresentationOutput,
    DashboardRequest,
)
from app.dashboard.pipeline import run_dashboard_pipeline
from app.dashboard.validate_input import validate_dashboard_request
from app.premarket.morning_briefing import BriefingCollection


def assemble_dashboard(
    request: DashboardRequest | object,
) -> DashboardPresentationOutput:
    """Assemble a Dashboard presentation under Policy Version v1."""
    validated_model = _coerce_request(request)
    validated = validate_dashboard_request(validated_model)
    return run_dashboard_pipeline(validated)


def assemble_dashboard_from_parts(
    *,
    briefing: BriefingCollection | object,
    as_of: datetime,
    config: DashboardConfig | object | None = None,
) -> DashboardPresentationOutput:
    """Convenience entrypoint that coerces Dashboard parts into DashboardRequest."""
    if not isinstance(as_of, datetime):
        raise DashboardValidationError(detail="invalid_as_of")
    resolved_briefing = (
        briefing
        if isinstance(briefing, BriefingCollection)
        else BriefingCollection.model_validate(briefing)
    )
    request = DashboardRequest(
        briefing=resolved_briefing,
        as_of=as_of,
        config=(
            DashboardConfig()
            if config is None
            else (
                config
                if isinstance(config, DashboardConfig)
                else DashboardConfig.model_validate(config)
            )
        ),
    )
    return assemble_dashboard(request)


def _coerce_request(request: object) -> DashboardRequest:
    if isinstance(request, DashboardRequest):
        return request
    try:
        return DashboardRequest.model_validate(request)
    except Exception as exc:
        raise DashboardValidationError(detail=f"invalid_request:{exc}") from exc
