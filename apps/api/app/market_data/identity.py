"""Effective-dated canonical instrument identity."""

from __future__ import annotations

from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.market_data.enums import AssetClass
from app.market_data.timing import require_utc_aware


class InstrumentId(BaseModel):
    """Canonical instrument identity — provider symbols are never identity.

    ``instrument_key`` is the stable Bergama identifier. ``local_symbol`` is an
    effective-dated display/trading symbol binding, not identity.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    instrument_key: str = Field(min_length=1, max_length=128)
    asset_class: AssetClass
    local_symbol: str | None = Field(default=None, max_length=64)
    symbol_effective_from: datetime
    symbol_effective_to: datetime | None = None

    @field_validator("instrument_key")
    @classmethod
    def strip_key(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "instrument_key must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator("local_symbol")
    @classmethod
    def strip_symbol(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        return text or None

    @field_validator("symbol_effective_from", "symbol_effective_to")
    @classmethod
    def utc_dates(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return require_utc_aware(value, field_name="symbol_effective_*")

    @model_validator(mode="after")
    def validate_effective_window(self) -> Self:
        end = self.symbol_effective_to
        if end is not None and end < self.symbol_effective_from:
            msg = "symbol_effective_to must be >= symbol_effective_from"
            raise ValueError(msg)
        return self

    def is_effective_at(self, instant: datetime) -> bool:
        """Return whether the local_symbol binding applies at ``instant``."""
        moment = require_utc_aware(instant, field_name="instant")
        if moment < self.symbol_effective_from:
            return False
        return self.symbol_effective_to is None or moment <= self.symbol_effective_to
