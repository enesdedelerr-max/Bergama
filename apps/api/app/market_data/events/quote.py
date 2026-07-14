"""Canonical quote event."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal, Self

from pydantic import field_validator, model_validator

from app.market_data.enums import MarketEventType
from app.market_data.events.base import MarketEventBase
from app.market_data.money import require_finite_decimal


class QuoteEvent(MarketEventBase):
    """Top-of-book / NBBO-style quote."""

    event_type: Literal[MarketEventType.QUOTE] = MarketEventType.QUOTE
    bid_price: Decimal
    ask_price: Decimal
    bid_size: Decimal
    ask_size: Decimal

    @field_validator("bid_price", "ask_price", mode="before")
    @classmethod
    def parse_prices(cls, value: object, info: Any) -> Decimal:
        field_name = str(info.field_name)
        decimal_value = require_finite_decimal(value, field_name=field_name)  # type: ignore[arg-type]
        if decimal_value <= 0:
            msg = f"{field_name} must be > 0"
            raise ValueError(msg)
        return decimal_value

    @field_validator("bid_size", "ask_size", mode="before")
    @classmethod
    def parse_sizes(cls, value: object, info: Any) -> Decimal:
        field_name = str(info.field_name)
        decimal_value = require_finite_decimal(value, field_name=field_name)  # type: ignore[arg-type]
        if decimal_value < 0:
            msg = f"{field_name} must be >= 0"
            raise ValueError(msg)
        return decimal_value

    @model_validator(mode="after")
    def validate_quote(self) -> Self:
        if self.bid_price > self.ask_price:
            msg = "bid_price must be <= ask_price"
            raise ValueError(msg)
        if self.currency is None:
            msg = "currency is required for QuoteEvent"
            raise ValueError(msg)
        if self.venue is None:
            msg = "venue is required for QuoteEvent"
            raise ValueError(msg)
        return self
