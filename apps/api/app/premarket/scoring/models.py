"""Immutable Premarket Scoring Foundation contracts."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from app.market_data.money import require_finite_decimal
from app.market_data.timing import require_utc_aware
from app.premarket.catalyst.models import CatalystCollection
from app.premarket.gap.models import GapCollection
from app.premarket.scoring.policy import (
    ORDERING_POLICY_SCORE_DESC_INSTRUMENT_KEY_ASC_ID_ASC,
    POLICY_VERSION_V1,
    SCORE_QUANTIZE_POLICY_ID,
    WEIGHT_PROFILE_DEFAULT_V1,
)
from app.premarket.watchlist.models import Watchlist


class ScoreConfig(BaseModel):
    """Explicit Premarket scoring configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_version_id: str = Field(default=POLICY_VERSION_V1, min_length=1, max_length=128)
    weight_profile_id: str = Field(
        default=WEIGHT_PROFILE_DEFAULT_V1,
        min_length=1,
        max_length=128,
    )
    ordering_policy_id: str = Field(
        default=ORDERING_POLICY_SCORE_DESC_INSTRUMENT_KEY_ASC_ID_ASC,
        min_length=1,
        max_length=128,
    )
    score_quantize_policy_id: str = Field(
        default=SCORE_QUANTIZE_POLICY_ID,
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

    @field_validator("weight_profile_id")
    @classmethod
    def validate_weight_profile(cls, value: str) -> str:
        text = value.strip()
        if text != WEIGHT_PROFILE_DEFAULT_V1:
            msg = f"unsupported weight_profile_id: {text}"
            raise ValueError(msg)
        return text

    @field_validator("ordering_policy_id")
    @classmethod
    def validate_ordering_policy(cls, value: str) -> str:
        text = value.strip()
        if text != ORDERING_POLICY_SCORE_DESC_INSTRUMENT_KEY_ASC_ID_ASC:
            msg = f"unsupported ordering_policy_id: {text}"
            raise ValueError(msg)
        return text

    @field_validator("score_quantize_policy_id")
    @classmethod
    def validate_quantize_policy(cls, value: str) -> str:
        text = value.strip()
        if text != SCORE_QUANTIZE_POLICY_ID:
            msg = f"unsupported score_quantize_policy_id: {text}"
            raise ValueError(msg)
        return text


class ScoreRequest(BaseModel):
    """Immutable Premarket scoring input."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    watchlist: Watchlist
    as_of: datetime
    config: ScoreConfig
    catalysts: CatalystCollection | None = None
    gaps: GapCollection | None = None

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")


class ScoreComponents(BaseModel):
    """Feature components contributing to a Premarket Score."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    watchlist_rank: Decimal
    gap_magnitude: Decimal | None = None
    catalyst_presence: Decimal | None = None

    @field_validator("watchlist_rank", mode="before")
    @classmethod
    def parse_watchlist_rank(cls, value: object) -> Decimal:
        return _require_unit_interval_decimal(value, field_name="watchlist_rank")

    @field_validator("gap_magnitude", "catalyst_presence", mode="before")
    @classmethod
    def parse_optional_decimals(cls, value: object, info: ValidationInfo) -> Decimal | None:
        if value is None:
            return None
        return _require_unit_interval_decimal(value, field_name=str(info.field_name))


def _require_unit_interval_decimal(value: object, *, field_name: str) -> Decimal:
    """Parse a finite Decimal in ``[0, 1]``; never clamp or repair."""
    parsed = require_finite_decimal(value, field_name=field_name)  # type: ignore[arg-type]
    if parsed < Decimal("0") or parsed > Decimal("1"):
        msg = f"{field_name} must be a finite Decimal in [0, 1]"
        raise ValueError(msg)
    return parsed


class ScoreRecord(BaseModel):
    """One deterministic Premarket Score observation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    score_record_id: str = Field(min_length=64, max_length=64)
    instrument_key: str = Field(min_length=1, max_length=128)
    local_symbol: str | None = Field(default=None, max_length=64)
    score: Decimal
    components: ScoreComponents
    policy_version_id: str = Field(min_length=1, max_length=128)
    weight_profile_id: str = Field(min_length=1, max_length=128)
    as_of: datetime
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
        return require_finite_decimal(value, field_name="score")  # type: ignore[arg-type]

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")


class ScoreProvenance(BaseModel):
    """Replay-relevant Premarket Score collection provenance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    config_fingerprint: str = Field(min_length=64, max_length=64)
    input_fingerprint: str = Field(min_length=64, max_length=64)
    ordering_policy_id: str = Field(min_length=1, max_length=128)
    policy_version_id: str = Field(min_length=1, max_length=128)
    weight_profile_id: str = Field(min_length=1, max_length=128)
    source_identifiers: tuple[str, ...] = ()

    @field_validator("config_fingerprint", "input_fingerprint")
    @classmethod
    def require_sha256_hex(cls, value: str) -> str:
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "fingerprint must be sha256 hex"
            raise ValueError(msg)
        return text


class ScoreCollection(BaseModel):
    """Deterministic Premarket Score scan output."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    as_of: datetime
    records: tuple[ScoreRecord, ...]
    provenance: ScoreProvenance

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")
