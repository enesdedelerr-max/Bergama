"""Portfolio accounting policy."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.portfolio.decimal import (
    MONEY_QUANTUM,
    PNL_QUANTUM,
    PRICE_QUANTUM,
    QUANTITY_QUANTUM,
    canonical_decimal,
)
from app.strategy.keys import strategy_sha256


class PortfolioPolicy(BaseModel):
    """Deterministic accounting configuration for one portfolio."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_version: str = Field(default="1.0.0", min_length=1, max_length=32)
    base_currency: str = Field(default="USD", min_length=3, max_length=3)
    allow_short_positions: bool = False
    enforce_non_negative_cash: bool = False
    cleanup_zero_positions: bool = True
    quantity_quantum: str = canonical_decimal(QUANTITY_QUANTUM)
    price_quantum: str = canonical_decimal(PRICE_QUANTUM)
    money_quantum: str = canonical_decimal(MONEY_QUANTUM)
    pnl_quantum: str = canonical_decimal(PNL_QUANTUM)
    rounding_mode: str = "ROUND_HALF_EVEN"

    @field_validator("base_currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        text = value.strip().upper()
        if len(text) != 3 or not text.isalpha():
            msg = "base_currency must be a 3-letter ISO code"
            raise ValueError(msg)
        return text

    def fingerprint(self) -> str:
        payload: dict[str, Any] = self.model_dump(mode="python")
        return strategy_sha256(payload)
