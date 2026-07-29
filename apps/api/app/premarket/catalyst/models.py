"""Immutable Catalyst Foundation contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.market_data.events.news import NewsEvent
from app.market_data.timing import require_utc_aware
from app.premarket.catalyst.ordering import (
    ORDERING_POLICY_KNOWN_AT_ASC_EVENT_TIME_ASC_TYPE_ASC_INSTRUMENT_KEY_ASC_ID_ASC,
)


class CatalystClassificationRule(BaseModel):
    """Explicit topic → catalyst_type mapping rule."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str = Field(min_length=1, max_length=128)
    rule_priority: int
    catalyst_type: str = Field(min_length=1, max_length=64)
    match_topics: tuple[str, ...] = Field(min_length=1)

    @field_validator("rule_id", "catalyst_type")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "rule fields must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator("match_topics")
    @classmethod
    def normalize_topics(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized: list[str] = []
        seen: set[str] = set()
        for raw in value:
            topic = raw.strip().lower()
            if not topic:
                msg = "match_topics must not contain empty entries"
                raise ValueError(msg)
            if topic in seen:
                msg = f"match_topics contains duplicate topic: {topic}"
                raise ValueError(msg)
            seen.add(topic)
            normalized.append(topic)
        return tuple(normalized)


class CatalystConfig(BaseModel):
    """Explicit catalyst normalization configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    classification_rules: tuple[CatalystClassificationRule, ...] = Field(min_length=1)
    ordering_policy_id: str = Field(
        default=ORDERING_POLICY_KNOWN_AT_ASC_EVENT_TIME_ASC_TYPE_ASC_INSTRUMENT_KEY_ASC_ID_ASC,
        min_length=1,
        max_length=128,
    )

    @field_validator("ordering_policy_id")
    @classmethod
    def validate_ordering_policy(cls, value: str) -> str:
        text = value.strip()
        if text != ORDERING_POLICY_KNOWN_AT_ASC_EVENT_TIME_ASC_TYPE_ASC_INSTRUMENT_KEY_ASC_ID_ASC:
            msg = f"unsupported ordering_policy_id: {text}"
            raise ValueError(msg)
        return text

    @model_validator(mode="after")
    def validate_unique_rule_ids(self) -> Self:
        rule_ids = [rule.rule_id for rule in self.classification_rules]
        if len(rule_ids) != len(set(rule_ids)):
            msg = "classification_rules must have unique rule_id values"
            raise ValueError(msg)
        return self


class CatalystNormalizationRequest(BaseModel):
    """Immutable normalization input.

    Upstream events are canonical Market Data ``NewsEvent`` instances only.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    events: tuple[NewsEvent, ...]
    as_of: datetime
    config: CatalystConfig

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")


class CatalystRecord(BaseModel):
    """One normalized catalyst observation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    catalyst_record_id: str = Field(min_length=64, max_length=64)
    source_event_id: str | None = Field(default=None, max_length=256)
    source_content_fingerprint: str = Field(min_length=64, max_length=64)
    instrument_key: str | None = Field(default=None, max_length=128)
    local_symbol: str | None = Field(default=None, max_length=64)
    catalyst_type: str = Field(min_length=1, max_length=64)
    event_time: datetime
    known_at: datetime
    as_of: datetime
    source_provider: str = Field(min_length=1, max_length=64)
    rule_id: str = Field(min_length=1, max_length=128)

    @field_validator(
        "catalyst_record_id",
        "source_content_fingerprint",
    )
    @classmethod
    def require_sha256_hex(cls, value: str) -> str:
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "fingerprint must be sha256 hex"
            raise ValueError(msg)
        return text

    @field_validator("event_time", "known_at", "as_of")
    @classmethod
    def require_utc_timestamps(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="timestamp")


class CatalystProvenance(BaseModel):
    """Replay-relevant catalyst collection provenance."""

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


class CatalystCollection(BaseModel):
    """Deterministic normalized catalyst collection."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    as_of: datetime
    records: tuple[CatalystRecord, ...]
    provenance: CatalystProvenance

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")
