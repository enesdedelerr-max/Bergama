"""Portfolio Aggregate settings (#402).

Disabled by default. Enabling constructs only the in-memory service boundary:
no account creation, no broker/order/risk behavior, no Kafka/database adapter,
and no automatic portfolio mutation on startup.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PortfolioSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    enabled: bool = False
    base_currency: str = Field(default="USD", min_length=3, max_length=3)
    allow_short_positions: bool = False
    enforce_non_negative_cash: bool = False
    audit_max_records: int = Field(default=10_000, ge=1, le=1_000_000)
    lock_timeout_seconds: float = Field(default=5.0, gt=0, le=300)

    @field_validator("base_currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        text = value.strip().upper()
        if len(text) != 3 or not text.isalpha():
            msg = "base_currency must be a 3-letter ISO code"
            raise ValueError(msg)
        return text

    def safe_summary(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "base_currency": self.base_currency,
            "allow_short_positions": self.allow_short_positions,
            "enforce_non_negative_cash": self.enforce_non_negative_cash,
            "audit_max_records": self.audit_max_records,
            "lock_timeout_seconds": self.lock_timeout_seconds,
        }
