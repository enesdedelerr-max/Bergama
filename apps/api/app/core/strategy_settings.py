"""Strategy Engine settings (#401).

Disabled by default. Settings create no sessions, no live startup, no broker
adapter, and no dynamic strategy loading.
"""

from __future__ import annotations

from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrategySettings(BaseModel):
    """Typed Strategy Engine configuration with safe foundation defaults."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    enabled: bool = False
    register_reference_strategy: bool = True
    max_strategies_per_session: int = Field(default=16, ge=1, le=128)
    max_seen_inputs_per_session: int = Field(default=100_000, ge=1, le=1_000_000)
    audit_max_records: int = Field(default=10_000, ge=1, le=1_000_000)
    require_downstream_port: bool = True
    allow_degraded_inputs: bool = True

    @model_validator(mode="after")
    def validate_semantics(self) -> Self:
        if self.enabled and not self.require_downstream_port:
            msg = "Strategy Engine requires an explicit downstream decision port"
            raise ValueError(msg)
        return self

    def safe_summary(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "register_reference_strategy": self.register_reference_strategy,
            "max_strategies_per_session": self.max_strategies_per_session,
            "max_seen_inputs_per_session": self.max_seen_inputs_per_session,
            "audit_max_records": self.audit_max_records,
            "require_downstream_port": self.require_downstream_port,
            "allow_degraded_inputs": self.allow_degraded_inputs,
        }
