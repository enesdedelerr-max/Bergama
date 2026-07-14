"""Canonical OHLCV bar event."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal, Self

from pydantic import Field, field_validator, model_validator

from app.market_data.enums import MarketEventType
from app.market_data.events.base import MarketEventBase
from app.market_data.money import require_finite_decimal
from app.market_data.timing import require_utc_aware


class BarEvent(MarketEventBase):
    """OHLCV bar with explicit observation window and close time."""

    event_type: Literal[MarketEventType.BAR] = MarketEventType.BAR
    window_start: datetime
    window_end: datetime
    close_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    vwap: Decimal | None = None
    trade_count: int | None = Field(default=None, ge=0)

    @field_validator("window_start", "window_end", "close_time")
    @classmethod
    def utc_window(cls, value: datetime, info: Any) -> datetime:
        return require_utc_aware(value, field_name=str(info.field_name))

    @field_validator("open", "high", "low", "close", mode="before")
    @classmethod
    def parse_prices(cls, value: object, info: Any) -> Decimal:
        field_name = str(info.field_name)
        decimal_value = require_finite_decimal(value, field_name=field_name)  # type: ignore[arg-type]
        if decimal_value <= 0:
            msg = f"{field_name} must be > 0"
            raise ValueError(msg)
        return decimal_value

    @field_validator("volume", mode="before")
    @classmethod
    def parse_volume(cls, value: object) -> Decimal:
        decimal_value = require_finite_decimal(value, field_name="volume")  # type: ignore[arg-type]
        if decimal_value < 0:
            msg = "volume must be >= 0"
            raise ValueError(msg)
        return decimal_value

    @field_validator("vwap", mode="before")
    @classmethod
    def parse_vwap(cls, value: object) -> Decimal | None:
        if value is None:
            return None
        decimal_value = require_finite_decimal(value, field_name="vwap")  # type: ignore[arg-type]
        if decimal_value <= 0:
            msg = "vwap must be > 0 when set"
            raise ValueError(msg)
        return decimal_value

    @model_validator(mode="after")
    def validate_bar(self) -> Self:
        if self.window_end < self.window_start:
            msg = "window_end must be >= window_start"
            raise ValueError(msg)
        if not (self.window_start <= self.close_time <= self.window_end):
            msg = "close_time must lie within [window_start, window_end]"
            raise ValueError(msg)
        if self.high < self.low:
            msg = "high must be >= low"
            raise ValueError(msg)
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            msg = "open/close must lie within [low, high]"
            raise ValueError(msg)
        if self.currency is None:
            msg = "currency is required for BarEvent"
            raise ValueError(msg)
        # occurred_at should normally align with close_time for bars.
        if self.occurred_at != self.close_time:
            msg = "BarEvent.occurred_at must equal close_time"
            raise ValueError(msg)
        return self
