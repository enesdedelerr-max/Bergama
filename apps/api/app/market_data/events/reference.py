"""Canonical reference-data event."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import Field, field_validator, model_validator

from app.market_data.enums import MarketEventType
from app.market_data.events.base import MarketEventBase


class ReferenceDataEvent(MarketEventBase):
    """Point-in-time reference / instrument master facts."""

    event_type: Literal[MarketEventType.REFERENCE_DATA] = MarketEventType.REFERENCE_DATA
    name: str | None = Field(default=None, max_length=256)
    exchange_mic: str | None = Field(default=None, max_length=16)
    isin: str | None = Field(default=None, max_length=16)
    cusip: str | None = Field(default=None, max_length=16)
    status: str | None = Field(default=None, max_length=32)
    attributes: dict[str, str] = Field(default_factory=dict)

    @field_validator("name", "exchange_mic", "isin", "cusip", "status")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        return text or None

    @model_validator(mode="after")
    def validate_reference(self) -> Self:
        if len(self.attributes) > 64:
            msg = "attributes may contain at most 64 entries"
            raise ValueError(msg)
        for key, value in self.attributes.items():
            if not str(key).strip() or len(str(value)) > 512:
                msg = "invalid attributes entry"
                raise ValueError(msg)
        return self
