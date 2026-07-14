"""Canonical macro / economic indicator event."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import Field, field_validator

from app.market_data.enums import MarketEventType
from app.market_data.events.base import MarketEventBase
from app.market_data.money import require_finite_decimal


class MacroEvent(MarketEventBase):
    """Macro series observation (FRED-style inputs map here after normalization)."""

    event_type: Literal[MarketEventType.MACRO] = MarketEventType.MACRO
    series_id: str = Field(min_length=1, max_length=64)
    value: Decimal
    unit: str | None = Field(default=None, max_length=32)
    frequency: str | None = Field(default=None, max_length=32)

    @field_validator("series_id", "unit", "frequency")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        return text or None

    @field_validator("value", mode="before")
    @classmethod
    def parse_value(cls, value: object) -> Decimal:
        return require_finite_decimal(value, field_name="value")  # type: ignore[arg-type]
