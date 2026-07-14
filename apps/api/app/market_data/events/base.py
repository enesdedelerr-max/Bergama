"""Shared fields for all canonical market events."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.market_data.enums import AdjustmentState
from app.market_data.identity import InstrumentId
from app.market_data.quality import DataQualityFlags
from app.market_data.source import SourceReference
from app.market_data.timing import require_utc_aware, validate_point_in_time_order

_MAX_METADATA = 32
_MAX_METADATA_KEY = 64
_MAX_METADATA_VALUE = 512


class MarketEventBase(BaseModel):
    """Common PIT, identity, source, quality and schema metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = Field(min_length=1, max_length=32)
    instrument: InstrumentId
    source: SourceReference
    quality: DataQualityFlags = Field(default_factory=DataQualityFlags)
    adjustment_state: AdjustmentState = AdjustmentState.UNADJUSTED
    occurred_at: datetime
    effective_at: datetime
    known_at: datetime
    ingested_at: datetime
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    venue: str | None = Field(default=None, max_length=32)
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("schema_version")
    @classmethod
    def strip_schema(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "schema_version must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip().upper()
        if len(text) != 3 or not text.isalpha():
            msg = "currency must be a 3-letter ISO code when provided"
            raise ValueError(msg)
        return text

    @field_validator("venue")
    @classmethod
    def strip_venue(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip().upper()
        return text or None

    @field_validator("occurred_at", "effective_at", "known_at", "ingested_at")
    @classmethod
    def utc_timestamps(cls, value: datetime, info: Any) -> datetime:
        return require_utc_aware(value, field_name=str(info.field_name))

    @model_validator(mode="after")
    def validate_common(self) -> Self:
        validate_point_in_time_order(
            occurred_at=self.occurred_at,
            effective_at=self.effective_at,
            known_at=self.known_at,
            ingested_at=self.ingested_at,
            quality=self.quality,
        )
        if len(self.metadata) > _MAX_METADATA:
            msg = f"metadata may contain at most {_MAX_METADATA} entries"
            raise ValueError(msg)
        cleaned: dict[str, str] = {}
        for key, value in self.metadata.items():
            k = str(key).strip()
            v = str(value).strip()
            if not k or len(k) > _MAX_METADATA_KEY or len(v) > _MAX_METADATA_VALUE:
                msg = "metadata keys/values exceed allowed bounds"
                raise ValueError(msg)
            lowered = k.lower()
            if any(token in lowered for token in ("password", "secret", "token", "api_key")):
                msg = f"forbidden metadata key {k!r}"
                raise ValueError(msg)
            cleaned[k] = v
        object.__setattr__(self, "metadata", cleaned)
        return self
