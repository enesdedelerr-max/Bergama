"""Order policy — bounded history and schema fingerprint only."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.orders.identity import ORDER_SCHEMA_VERSION
from app.strategy.keys import strategy_sha256


class OrderPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_version: str = Field(default="1.0.0", min_length=1, max_length=32)
    order_schema_version: str = Field(default=ORDER_SCHEMA_VERSION, min_length=1, max_length=64)
    max_fill_history: int = Field(default=1_000, ge=1, le=100_000)
    max_broker_event_history: int = Field(default=1_000, ge=1, le=100_000)
    max_domain_event_history: int = Field(default=2_000, ge=1, le=100_000)

    def fingerprint(self) -> str:
        payload: dict[str, Any] = self.model_dump(mode="python")
        return strategy_sha256(payload)
