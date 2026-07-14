"""Canonical fundamental event."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal, Self

from pydantic import Field, field_validator, model_validator

from app.market_data.enums import MarketEventType
from app.market_data.events.base import MarketEventBase
from app.market_data.money import require_finite_decimal


class FundamentalEvent(MarketEventBase):
    """Company fundamental observation (ratio / statement line)."""

    event_type: Literal[MarketEventType.FUNDAMENTAL] = MarketEventType.FUNDAMENTAL
    metric_code: str = Field(min_length=1, max_length=64)
    period: str = Field(min_length=1, max_length=32)
    value: Decimal
    unit: str | None = Field(default=None, max_length=32)

    @field_validator("metric_code", "period", "unit")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if not text:
            msg = "value must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator("value", mode="before")
    @classmethod
    def parse_value(cls, value: object) -> Decimal:
        # Fundamentals may be negative (e.g. net income). Zero allowed.
        return require_finite_decimal(value, field_name="value")  # type: ignore[arg-type]

    @model_validator(mode="after")
    def require_currency_when_money(self) -> Self:
        if self.unit in {"currency", "money", "usd", "monetary"} and self.currency is None:
            msg = "currency is required when unit denotes money"
            raise ValueError(msg)
        return self


_ = Any
