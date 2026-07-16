"""Risk Engine settings (#403).

Disabled by default. Enabling constructs only the pure evaluator boundary:
no startup evaluation, no Kafka/database adapter, no broker/OMS behavior,
and no portfolio or strategy mutation.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RiskSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    enabled: bool = False
    audit_max_records: int = Field(default=10_000, ge=1, le=1_000_000)
    require_downstream_port: bool = False

    def safe_summary(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "audit_max_records": self.audit_max_records,
            "require_downstream_port": self.require_downstream_port,
        }
