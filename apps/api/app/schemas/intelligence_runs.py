"""Strict public DTOs for Intelligence Run product read API (WS3)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.ai_decision_engine.models import AdeOutcomeKind
from app.ai_decision_engine.reasons import AdeReasonFamily
from app.dashboard.models import DashboardPresentationOutput
from app.human_review.models import HumanReviewOutput
from app.market_data.timing import require_utc_aware


class ProductErrorResponse(BaseModel):
    """Frozen public product error body."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    details: dict[str, Any] | None = None


class AdeProductProvenanceRead(BaseModel):
    """ADE provenance public fields without recorded attestation payload."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_version_id: str = Field(min_length=1, max_length=128)
    identity_specification_id: str = Field(min_length=1, max_length=128)
    provenance_specification_id: str = Field(min_length=1, max_length=128)
    acceptance_specification_id: str = Field(min_length=1, max_length=128)
    digest_method_id: str = Field(min_length=1, max_length=128)
    derivation_attribution_id: str = Field(min_length=1, max_length=128)
    as_of: datetime
    human_review_output_id: str | None = Field(default=None, min_length=64, max_length=64)
    human_review_policy_version_id: str | None = Field(default=None, min_length=1, max_length=128)
    human_review_identity_specification_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
    )
    human_review_provenance_specification_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
    )
    human_review_config_fingerprint: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )
    human_review_input_fingerprint: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )
    recorded_attestation_fingerprint: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )
    config_fingerprint: str = Field(min_length=64, max_length=64)
    evidence_fingerprint: str = Field(min_length=64, max_length=64)

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")


class AdeProductSnapshotRead(BaseModel):
    """Bounded ADE public product snapshot (payload excluded)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome_kind: AdeOutcomeKind
    policy_version_id: str = Field(min_length=1, max_length=128)
    as_of: datetime
    reason_family: AdeReasonFamily
    decision_id: str | None = Field(default=None, min_length=64, max_length=64)
    human_review_output_id: str | None = Field(default=None, min_length=64, max_length=64)
    provenance: AdeProductProvenanceRead
    detail: str | None = None

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")


class IntelligenceRunRead(BaseModel):
    """Public Intelligence Run read DTO."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=36, max_length=36)
    pipeline_fingerprint: str | None = None
    as_of: datetime | None = None
    persisted_at: datetime
    snapshot_contract_version: str = Field(min_length=1)
    persistence_schema_version: str = Field(min_length=1)
    age_seconds: int = Field(ge=0)
    outcome: str = Field(min_length=1)
    failed_stage: str | None = None
    failure_error_type: str | None = None
    failure_detail: str | None = None
    bindings: dict[str, Any] | None = None
    provenance: dict[str, Any]
    stage_presence: dict[str, str]
    dashboard: DashboardPresentationOutput | None = None
    human_review: HumanReviewOutput | None = None
    ade: AdeProductSnapshotRead | None = None

    @field_validator("as_of", "persisted_at")
    @classmethod
    def require_utc_timestamps(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return require_utc_aware(value, field_name="timestamp")


class IntelligenceRunDashboardRead(BaseModel):
    """Dashboard stage public subresource."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=36, max_length=36)
    dashboard: DashboardPresentationOutput


class IntelligenceRunHumanReviewRead(BaseModel):
    """Human Review stage public subresource."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=36, max_length=36)
    human_review: HumanReviewOutput


class IntelligenceRunAdeRead(BaseModel):
    """ADE stage public subresource."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=36, max_length=36)
    ade: AdeProductSnapshotRead
