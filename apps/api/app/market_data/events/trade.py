"""Canonical trade event."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal, Self

from pydantic import Field, field_validator, model_validator

from app.market_data.enums import MarketEventType
from app.market_data.events.base import MarketEventBase
from app.market_data.money import require_finite_decimal


class TradeEvent(MarketEventBase):
    """Last-sale / execution print."""

    event_type: Literal[MarketEventType.TRADE] = MarketEventType.TRADE
    price: Decimal
    size: Decimal
    trade_id: str | None = Field(default=None, max_length=128)
    aggressor_side: str | None = Field(default=None, max_length=16)

    @field_validator("price", mode="before")
    @classmethod
    def parse_price(cls, value: object) -> Decimal:
        decimal_value = require_finite_decimal(value, field_name="price")  # type: ignore[arg-type]
        if decimal_value <= 0:
            msg = "price must be > 0"
            raise ValueError(msg)
        return decimal_value

    @field_validator("size", mode="before")
    @classmethod
    def parse_size(cls, value: object) -> Decimal:
        decimal_value = require_finite_decimal(value, field_name="size")  # type: ignore[arg-type]
        if decimal_value <= 0:
            msg = "size must be > 0"
            raise ValueError(msg)
        return decimal_value

    @field_validator("trade_id", "aggressor_side")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        return text or None

    @field_validator("aggressor_side")
    @classmethod
    def validate_side(cls, value: str | None) -> str | None:
        if value is None:
            return None
        allowed = {"buy", "sell", "unknown"}
        lowered = value.lower()
        if lowered not in allowed:
            msg = "aggressor_side must be buy|sell|unknown when set"
            raise ValueError(msg)
        return lowered

    @model_validator(mode="after")
    def require_currency_venue(self) -> Self:
        if self.currency is None:
            msg = "currency is required for TradeEvent"
            raise ValueError(msg)
        if self.venue is None:
            msg = "venue is required for TradeEvent"
            raise ValueError(msg)
        return self


_ = Any
