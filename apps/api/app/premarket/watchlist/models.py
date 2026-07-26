"""Immutable Watchlist Engine contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.market_data.timing import require_utc_aware
from app.premarket.watchlist.ordering import ORDERING_POLICY_RULE_PRIORITY_ASC_INSTRUMENT_KEY_ASC


class WatchlistCandidate(BaseModel):
    """One ordered candidate instrument for watchlist generation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    instrument_key: str = Field(min_length=1, max_length=128)
    local_symbol: str | None = Field(default=None, max_length=64)

    @field_validator("instrument_key")
    @classmethod
    def strip_instrument_key(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "instrument_key must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator("local_symbol")
    @classmethod
    def strip_local_symbol(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        return text or None


class WatchlistInclusionRule(BaseModel):
    """Config-driven allowlist inclusion rule."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str = Field(min_length=1, max_length=128)
    rule_priority: int
    inclusion_reason: str = Field(min_length=1, max_length=256)
    allowed_instrument_keys: tuple[str, ...] = Field(min_length=1)

    @field_validator("rule_id", "inclusion_reason")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "rule fields must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator("allowed_instrument_keys")
    @classmethod
    def normalize_allowed_keys(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized: list[str] = []
        seen: set[str] = set()
        for raw in value:
            key = raw.strip()
            if not key:
                msg = "allowed_instrument_keys must not contain empty keys"
                raise ValueError(msg)
            if key in seen:
                msg = f"allowed_instrument_keys contains duplicate key: {key}"
                raise ValueError(msg)
            seen.add(key)
            normalized.append(key)
        return tuple(normalized)


class WatchlistConfig(BaseModel):
    """Explicit watchlist generation configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rules: tuple[WatchlistInclusionRule, ...] = Field(min_length=1)
    max_size: int | None = Field(default=None)
    ordering_policy_id: str = Field(
        default=ORDERING_POLICY_RULE_PRIORITY_ASC_INSTRUMENT_KEY_ASC,
        min_length=1,
        max_length=128,
    )

    @field_validator("ordering_policy_id")
    @classmethod
    def validate_ordering_policy(cls, value: str) -> str:
        text = value.strip()
        if text != ORDERING_POLICY_RULE_PRIORITY_ASC_INSTRUMENT_KEY_ASC:
            msg = f"unsupported ordering_policy_id: {text}"
            raise ValueError(msg)
        return text

    @field_validator("max_size")
    @classmethod
    def validate_max_size(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value <= 0:
            msg = "max_size must be positive when provided"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def validate_unique_rule_ids(self) -> Self:
        rule_ids = [rule.rule_id for rule in self.rules]
        if len(rule_ids) != len(set(rule_ids)):
            msg = "rules must have unique rule_id values"
            raise ValueError(msg)
        return self


class WatchlistGenerationRequest(BaseModel):
    """Immutable generation input.

    Feature Platform snapshots are intentionally omitted from v1. A future
    optional seam may be added without changing Market Data contracts.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidates: tuple[WatchlistCandidate, ...]
    as_of: datetime
    config: WatchlistConfig

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")


class WatchlistEntry(BaseModel):
    """One included watchlist instrument."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    instrument_key: str = Field(min_length=1, max_length=128)
    local_symbol: str | None = Field(default=None, max_length=64)
    evaluation_timestamp: datetime
    rank: int = Field(ge=1)
    inclusion_reason: str = Field(min_length=1, max_length=256)
    rule_id: str = Field(min_length=1, max_length=128)

    @field_validator("evaluation_timestamp")
    @classmethod
    def require_utc_evaluation(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="evaluation_timestamp")


class WatchlistProvenance(BaseModel):
    """Replay-relevant watchlist provenance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    config_fingerprint: str = Field(min_length=64, max_length=64)
    input_fingerprint: str = Field(min_length=64, max_length=64)
    ordering_policy_id: str = Field(min_length=1, max_length=128)
    source_identifiers: tuple[str, ...] = ()

    @field_validator("config_fingerprint", "input_fingerprint")
    @classmethod
    def require_sha256_hex(cls, value: str) -> str:
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "fingerprint must be sha256 hex"
            raise ValueError(msg)
        return text


class Watchlist(BaseModel):
    """Deterministic watchlist output."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    evaluation_timestamp: datetime
    entries: tuple[WatchlistEntry, ...]
    provenance: WatchlistProvenance

    @field_validator("evaluation_timestamp")
    @classmethod
    def require_utc_evaluation(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="evaluation_timestamp")
