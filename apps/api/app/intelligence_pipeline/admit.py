"""Fail-closed Intelligence Pipeline run admission."""

from __future__ import annotations

from pydantic import ValidationError

from app.intelligence_pipeline.errors import PipelineAdmissionError
from app.intelligence_pipeline.models import PipelineBindings, PipelineRequest
from app.intelligence_pipeline.policy import POLICY_VERSION_V1
from app.market_data.timing import require_utc_aware


def coerce_pipeline_request(request: PipelineRequest | object) -> PipelineRequest:
    """Admit only bounded typed Pipeline requests; reject unauthorized shapes."""
    if isinstance(request, PipelineRequest):
        return request
    if isinstance(request, dict) and any(
        key in request
        for key in (
            "model_output",
            "model_response",
            "prompt",
            "llm",
            "provider_payload",
            "broker",
            "order_intent",
            "oms",
            "human_review",
            "ade",
            "database",
            "feature_store",
            "http_request",
        )
    ):
        raise PipelineAdmissionError(detail="unsupported_unauthorized_input")
    try:
        return PipelineRequest.model_validate(request)
    except (ValidationError, ValueError, TypeError) as exc:
        raise PipelineAdmissionError(detail=f"invalid_request:{exc}") from exc


def admit_pipeline_request(request: PipelineRequest | object) -> PipelineRequest:
    """Validate and freeze the admitted Pipeline request for the run."""
    admitted = coerce_pipeline_request(request)
    try:
        require_utc_aware(admitted.as_of, field_name="as_of")
    except ValueError as exc:
        raise PipelineAdmissionError(detail=f"invalid_as_of:{exc}") from exc
    return admitted


def pin_bindings(request: PipelineRequest) -> PipelineBindings:
    """Pin governed stage Policy/config bindings at admission (stable for the run)."""
    return PipelineBindings(
        policy_version_id=POLICY_VERSION_V1,
        watchlist_ordering_policy_id=request.watchlist_config.ordering_policy_id,
        gap_selection_policy_id=request.gap_config.selection_policy_id,
        gap_ordering_policy_id=request.gap_config.ordering_policy_id,
        catalyst_ordering_policy_id=request.catalyst_config.ordering_policy_id,
        score_policy_version_id=request.score_config.policy_version_id,
        score_weight_profile_id=request.score_config.weight_profile_id,
        briefing_policy_version_id=request.briefing_config.policy_version_id,
        dashboard_policy_version_id=request.dashboard_config.policy_version_id,
    )
