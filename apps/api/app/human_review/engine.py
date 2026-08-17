"""Deterministic Human Review engine."""

from __future__ import annotations

from datetime import datetime

from app.dashboard.models import DashboardPresentationOutput
from app.human_review.errors import HumanReviewValidationError
from app.human_review.models import (
    HumanReviewConfig,
    HumanReviewOutput,
    HumanReviewRecordedAttestation,
    HumanReviewRequest,
)
from app.human_review.pipeline import run_human_review_pipeline
from app.human_review.validate_input import validate_human_review_request


def assemble_human_review(
    request: HumanReviewRequest | object,
) -> HumanReviewOutput:
    """Assemble a Human Review output under Policy Version v1."""
    validated_model = _coerce_request(request)
    validated = validate_human_review_request(validated_model)
    return run_human_review_pipeline(validated)


def assemble_human_review_from_parts(
    *,
    dashboard: DashboardPresentationOutput | object,
    as_of: datetime,
    attestation: HumanReviewRecordedAttestation | str | object,
    config: HumanReviewConfig | object | None = None,
) -> HumanReviewOutput:
    """Convenience entrypoint that coerces Human Review parts into HumanReviewRequest."""
    if not isinstance(as_of, datetime):
        raise HumanReviewValidationError(detail="invalid_as_of")
    resolved_dashboard = (
        dashboard
        if isinstance(dashboard, DashboardPresentationOutput)
        else DashboardPresentationOutput.model_validate(dashboard)
    )
    resolved_attestation = _coerce_attestation(attestation)
    request = HumanReviewRequest(
        dashboard=resolved_dashboard,
        as_of=as_of,
        config=(
            HumanReviewConfig()
            if config is None
            else (
                config
                if isinstance(config, HumanReviewConfig)
                else HumanReviewConfig.model_validate(config)
            )
        ),
        attestation=resolved_attestation,
    )
    return assemble_human_review(request)


def _coerce_attestation(
    attestation: HumanReviewRecordedAttestation | str | object,
) -> HumanReviewRecordedAttestation:
    if isinstance(attestation, HumanReviewRecordedAttestation):
        return attestation
    if isinstance(attestation, str):
        try:
            return HumanReviewRecordedAttestation(recorded_payload=attestation)
        except Exception as exc:
            raise HumanReviewValidationError(detail=f"invalid_attestation:{exc}") from exc
    try:
        return HumanReviewRecordedAttestation.model_validate(attestation)
    except Exception as exc:
        raise HumanReviewValidationError(detail=f"invalid_attestation:{exc}") from exc


def _coerce_request(request: object) -> HumanReviewRequest:
    if isinstance(request, HumanReviewRequest):
        return request
    try:
        return HumanReviewRequest.model_validate(request)
    except Exception as exc:
        raise HumanReviewValidationError(detail=f"invalid_request:{exc}") from exc
