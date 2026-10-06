"""Fail-closed Intelligence Pipeline run admission."""

from __future__ import annotations

from pydantic import ValidationError

from app.ai_decision_engine.models import AdeConfig
from app.core.premarket_settings import PremarketSettings
from app.human_review.models import HumanReviewConfig
from app.intelligence_pipeline.errors import PipelineAdmissionError
from app.intelligence_pipeline.models import PipelineBindings, PipelineRequest
from app.intelligence_pipeline.policy import (
    FINGERPRINT_SCHEMA_ID,
    IMPLEMENTATION_AUTHORIZATION_ID,
    POLICY_VERSION_V1,
)
from app.market_data.timing import require_utc_aware
from app.strategy.keys import strategy_sha256


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

    if admitted.ade_requested and not admitted.hr_requested:
        raise PipelineAdmissionError(detail="ade_requires_human_review")
    if admitted.hr_requested and admitted.hr_attestation is None:
        raise PipelineAdmissionError(detail="human_review_attestation_required")

    if admitted.settings is not None:
        # Isolate mutable PremarketSettings from caller-owned references (F-02).
        admitted = admitted.model_copy(
            update={
                "settings": PremarketSettings.model_validate(admitted.settings.model_dump()),
            }
        )
    return admitted


def resolve_hr_config(request: PipelineRequest) -> HumanReviewConfig:
    """Return admitted Human Review config without mutating the request."""
    if request.hr_config is not None:
        return request.hr_config
    return HumanReviewConfig()


def resolve_ade_config(request: PipelineRequest) -> AdeConfig:
    """Return admitted ADE config without mutating the request."""
    if request.ade_config is not None:
        return request.ade_config
    return AdeConfig()


def pin_bindings(request: PipelineRequest) -> PipelineBindings:
    """Pin governed stage Policy/config bindings at admission (stable for the run)."""
    human_review_policy_version_id: str | None = None
    ade_policy_version_id: str | None = None
    if request.hr_requested:
        human_review_policy_version_id = resolve_hr_config(request).policy_version_id
    if request.ade_requested:
        ade_policy_version_id = resolve_ade_config(request).policy_version_id
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
        human_review_policy_version_id=human_review_policy_version_id,
        ade_policy_version_id=ade_policy_version_id,
    )


def compute_pipeline_fingerprint(
    request: PipelineRequest,
    bindings: PipelineBindings,
) -> str:
    """Deterministic input/composition identity (SHA-256 hex). Tooling-only hash reuse."""
    return strategy_sha256(
        {
            "fingerprint_schema_id": FINGERPRINT_SCHEMA_ID,
            "policy_version_id": POLICY_VERSION_V1,
            "implementation_authorization_id": IMPLEMENTATION_AUTHORIZATION_ID,
            "request": request.model_dump(mode="python"),
            "bindings": bindings.model_dump(mode="python"),
        }
    )
