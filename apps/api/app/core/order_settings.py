"""Order Management System settings (#404).

Disabled by default. Enabling constructs only the OMS service boundary:
no startup order creation, no broker submission, no Kafka/database adapter,
and no portfolio/strategy/risk mutation.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OrderSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    enabled: bool = False
    audit_max_records: int = Field(default=10_000, ge=1, le=1_000_000)
    lock_timeout_seconds: float = Field(default=5.0, gt=0, le=300)
    max_history: int = Field(default=2_000, ge=1, le=100_000)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "audit_max_records": self.audit_max_records,
            "lock_timeout_seconds": self.lock_timeout_seconds,
            "max_history": self.max_history,
        }
