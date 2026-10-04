"""Immutable AI Decision Engine Policy Version v1 contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.ai_decision_engine.policy import (
    ACCEPTANCE_SPECIFICATION_V1,
    DERIVATION_ATTRIBUTION_V1,
    DIGEST_METHOD_V1,
    IDENTITY_SPECIFICATION_V1,
    POLICY_VERSION_V1,
    PROVENANCE_SPECIFICATION_V1,
)
from app.ai_decision_engine.reasons import FROZEN_REASON_FAMILIES, AdeReasonFamily
from app.human_review import HumanReviewOutput
from app.market_data.timing import require_utc_aware


class AdeOutcomeKind(StrEnum):
    """Frozen minimum ADE outcome distinction."""

    AUTHORITATIVE_DECISION = "authoritative_decision"
    EXPLICIT_ABSTENTION = "explicit_abstention"


class AdeConfig(BaseModel):
    """Explicit ADE evaluation configuration bound to Policy Version v1."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_version_id: str = Field(default=POLICY_VERSION_V1, min_length=1, max_length=128)
    identity_specification_id: str = Field(
        default=IDENTITY_SPECIFICATION_V1,
        min_length=1,
        max_length=128,
    )
    provenance_specification_id: str = Field(
        default=PROVENANCE_SPECIFICATION_V1,
        min_length=1,
        max_length=128,
    )
    acceptance_specification_id: str = Field(
        default=ACCEPTANCE_SPECIFICATION_V1,
        min_length=1,
        max_length=128,
    )
    digest_method_id: str = Field(default=DIGEST_METHOD_V1, min_length=1, max_length=128)
    derivation_attribution_id: str = Field(
        default=DERIVATION_ATTRIBUTION_V1,
        min_length=1,
        max_length=128,
    )

    @field_validator("policy_version_id")
    @classmethod
    def validate_policy_version(cls, value: str) -> str:
        text = value.strip()
        if text != POLICY_VERSION_V1:
            msg = f"unsupported policy_version_id: {text}"
            raise ValueError(msg)
        return text

    @field_validator("identity_specification_id")
    @classmethod
    def validate_identity_specification(cls, value: str) -> str:
        text = value.strip()
        if text != IDENTITY_SPECIFICATION_V1:
            msg = f"unsupported identity_specification_id: {text}"
            raise ValueError(msg)
        return text

    @field_validator("provenance_specification_id")
    @classmethod
    def validate_provenance_specification(cls, value: str) -> str:
        text = value.strip()
        if text != PROVENANCE_SPECIFICATION_V1:
            msg = f"unsupported provenance_specification_id: {text}"
            raise ValueError(msg)
        return text

    @field_validator("acceptance_specification_id")
    @classmethod
    def validate_acceptance_specification(cls, value: str) -> str:
        text = value.strip()
        if text != ACCEPTANCE_SPECIFICATION_V1:
            msg = f"unsupported acceptance_specification_id: {text}"
            raise ValueError(msg)
        return text

    @field_validator("digest_method_id")
    @classmethod
    def validate_digest_method(cls, value: str) -> str:
        text = value.strip()
        if text != DIGEST_METHOD_V1:
            msg = f"unsupported digest_method_id: {text}"
            raise ValueError(msg)
        return text

    @field_validator("derivation_attribution_id")
    @classmethod
    def validate_derivation_attribution(cls, value: str) -> str:
        text = value.strip()
        if text != DERIVATION_ATTRIBUTION_V1:
            msg = f"unsupported derivation_attribution_id: {text}"
            raise ValueError(msg)
        return text


class AdeEvaluationRequest(BaseModel):
    """ADE evaluation context bound to explicit UTC ``as_of`` and HR public output."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    human_review: HumanReviewOutput | None
    as_of: datetime
    config: AdeConfig = Field(default_factory=AdeConfig)

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")


class AdeProvenance(BaseModel):
    """ADE provenance preserving Human Review references without ownership transfer."""

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
        default=None, min_length=1, max_length=128
    )
    human_review_provenance_specification_id: str | None = Field(
        default=None, min_length=1, max_length=128
    )
    human_review_config_fingerprint: str | None = Field(default=None, min_length=64, max_length=64)
    human_review_input_fingerprint: str | None = Field(default=None, min_length=64, max_length=64)
    recorded_attestation_fingerprint: str | None = Field(default=None, min_length=64, max_length=64)
    recorded_attestation_payload: str | None = None
    config_fingerprint: str = Field(min_length=64, max_length=64)
    evidence_fingerprint: str = Field(min_length=64, max_length=64)

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")

    @field_validator(
        "human_review_output_id",
        "human_review_config_fingerprint",
        "human_review_input_fingerprint",
        "recorded_attestation_fingerprint",
        "config_fingerprint",
        "evidence_fingerprint",
    )
    @classmethod
    def require_optional_sha256_hex(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "fingerprint must be sha256 hex"
            raise ValueError(msg)
        return text


class AdeResult(BaseModel):
    """Non-executing ADE foundation result: authoritative decision or explicit abstention."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome_kind: AdeOutcomeKind
    policy_version_id: str = Field(min_length=1, max_length=128)
    as_of: datetime
    reason_family: AdeReasonFamily
    decision_id: str | None = Field(default=None, min_length=64, max_length=64)
    human_review_output_id: str | None = Field(default=None, min_length=64, max_length=64)
    provenance: AdeProvenance
    detail: str | None = None

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")

    @field_validator("policy_version_id")
    @classmethod
    def validate_policy_version(cls, value: str) -> str:
        text = value.strip()
        if text != POLICY_VERSION_V1:
            msg = f"unsupported policy_version_id: {text}"
            raise ValueError(msg)
        return text

    @field_validator("reason_family", mode="before")
    @classmethod
    def validate_reason_family(cls, value: object) -> object:
        text = value.value if isinstance(value, AdeReasonFamily) else str(value)
        if text not in FROZEN_REASON_FAMILIES:
            msg = f"unauthorized reason family: {text}"
            raise ValueError(msg)
        return value

    @field_validator("decision_id", "human_review_output_id")
    @classmethod
    def require_optional_sha256_hex(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "identity must be sha256 hex"
            raise ValueError(msg)
        return text
