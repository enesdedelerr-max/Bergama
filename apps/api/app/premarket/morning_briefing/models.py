"""Immutable Morning Briefing Policy Version v1 contracts."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.market_data.money import require_finite_decimal
from app.market_data.timing import require_utc_aware
from app.premarket.morning_briefing.policy import (
    DIGEST_METHOD_V1,
    IDENTITY_SPECIFICATION_V1,
    ORDERING_PRESERVATION_POLICY_V1,
    POLICY_VERSION_V1,
    PROVENANCE_SPECIFICATION_V1,
)
from app.premarket.scoring.models import ScoreCollection, ScoreComponents
from app.premarket.scoring.policy import (
    POLICY_VERSION_V1 as SCORING_POLICY_VERSION_V1,
)
from app.premarket.scoring.policy import (
    WEIGHT_PROFILE_DEFAULT_V1,
)


class BriefingConfig(BaseModel):
    """Explicit Morning Briefing configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_version_id: str = Field(default=POLICY_VERSION_V1, min_length=1, max_length=128)
    ordering_preservation_policy_id: str = Field(
        default=ORDERING_PRESERVATION_POLICY_V1,
        min_length=1,
        max_length=128,
    )
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
    digest_method_id: str = Field(default=DIGEST_METHOD_V1, min_length=1, max_length=128)

    @field_validator("policy_version_id")
    @classmethod
    def validate_policy_version(cls, value: str) -> str:
        text = value.strip()
        if text != POLICY_VERSION_V1:
            msg = f"unsupported policy_version_id: {text}"
            raise ValueError(msg)
        return text

    @field_validator("ordering_preservation_policy_id")
    @classmethod
    def validate_ordering_preservation_policy(cls, value: str) -> str:
        text = value.strip()
        if text != ORDERING_PRESERVATION_POLICY_V1:
            msg = f"unsupported ordering_preservation_policy_id: {text}"
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

    @field_validator("digest_method_id")
    @classmethod
    def validate_digest_method(cls, value: str) -> str:
        text = value.strip()
        if text != DIGEST_METHOD_V1:
            msg = f"unsupported digest_method_id: {text}"
            raise ValueError(msg)
        return text


class BriefingRequest(BaseModel):
    """Immutable Morning Briefing input."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    scores: ScoreCollection
    as_of: datetime
    config: BriefingConfig

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")


class BriefingRecord(BaseModel):
    """One preserved Premarket Score reference inside a Morning Briefing."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    sequence_index: int = Field(ge=0)
    score_record_id: str = Field(min_length=64, max_length=64)
    instrument_key: str = Field(min_length=1, max_length=128)
    local_symbol: str | None = Field(default=None, max_length=64)
    score: Decimal
    components: ScoreComponents
    scoring_policy_version_id: str = Field(min_length=1, max_length=128)
    scoring_weight_profile_id: str = Field(min_length=1, max_length=128)
    scoring_as_of: datetime
    watchlist_rank: int = Field(ge=1)
    watchlist_rule_id: str = Field(min_length=1, max_length=128)
    gap_record_id: str | None = Field(default=None, max_length=64)
    catalyst_source_identifiers: tuple[str, ...] = ()

    @field_validator("score_record_id")
    @classmethod
    def require_sha256_hex(cls, value: str) -> str:
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "score_record_id must be sha256 hex"
            raise ValueError(msg)
        return text

    @field_validator("score", mode="before")
    @classmethod
    def parse_score(cls, value: object) -> Decimal:
        parsed = require_finite_decimal(value, field_name="score")  # type: ignore[arg-type]
        # Align with repository canonical Decimal convention (canonical_decimal_str):
        # negative zero is represented as Decimal("0") without clamping non-zero values.
        if parsed.is_zero():
            return Decimal("0")
        return parsed

    @field_validator("scoring_as_of")
    @classmethod
    def require_utc_scoring_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="scoring_as_of")

    @field_validator("scoring_policy_version_id")
    @classmethod
    def validate_scoring_policy_version(cls, value: str) -> str:
        text = value.strip()
        if text != SCORING_POLICY_VERSION_V1:
            msg = f"unsupported scoring_policy_version_id: {text}"
            raise ValueError(msg)
        return text

    @field_validator("scoring_weight_profile_id")
    @classmethod
    def validate_scoring_weight_profile(cls, value: str) -> str:
        text = value.strip()
        if text != WEIGHT_PROFILE_DEFAULT_V1:
            msg = f"unsupported scoring_weight_profile_id: {text}"
            raise ValueError(msg)
        return text


class BriefingProvenance(BaseModel):
    """Replay-relevant Morning Briefing provenance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_version_id: str = Field(min_length=1, max_length=128)
    ordering_preservation_policy_id: str = Field(min_length=1, max_length=128)
    identity_specification_id: str = Field(min_length=1, max_length=128)
    provenance_specification_id: str = Field(min_length=1, max_length=128)
    as_of: datetime
    config_fingerprint: str = Field(min_length=64, max_length=64)
    input_fingerprint: str = Field(min_length=64, max_length=64)
    source_identifiers: tuple[str, ...] = ()
    upstream_scoring_policy_version_id: str = Field(min_length=1, max_length=128)
    upstream_scoring_weight_profile_id: str = Field(min_length=1, max_length=128)
    upstream_scoring_ordering_policy_id: str = Field(min_length=1, max_length=128)
    upstream_scoring_config_fingerprint: str = Field(min_length=64, max_length=64)
    upstream_scoring_input_fingerprint: str = Field(min_length=64, max_length=64)

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")

    @field_validator(
        "config_fingerprint",
        "input_fingerprint",
        "upstream_scoring_config_fingerprint",
        "upstream_scoring_input_fingerprint",
    )
    @classmethod
    def require_sha256_hex(cls, value: str) -> str:
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "fingerprint must be sha256 hex"
            raise ValueError(msg)
        return text


class BriefingCollection(BaseModel):
    """Deterministic Morning Briefing output."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    briefing_id: str = Field(min_length=64, max_length=64)
    policy_version_id: str = Field(min_length=1, max_length=128)
    ordering_preservation_policy_id: str = Field(min_length=1, max_length=128)
    as_of: datetime
    records: tuple[BriefingRecord, ...]
    provenance: BriefingProvenance

    @field_validator("briefing_id")
    @classmethod
    def require_sha256_hex(cls, value: str) -> str:
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "briefing_id must be sha256 hex"
            raise ValueError(msg)
        return text

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")
