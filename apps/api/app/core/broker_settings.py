"""Broker abstraction settings (#405).

Disabled by default. Enabling constructs only the PaperBroker boundary:
no startup submit/cancel, no live SDK, no Kafka/database adapter,
and no portfolio/strategy/risk/OMS mutation by the adapter itself.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BrokerSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    enabled: bool = False
    broker_name: str = Field(default="paper", min_length=1, max_length=64)
    broker_account_id: str = Field(default="paper-account-1", min_length=1, max_length=128)
    simulation_seed: int = Field(default=0, ge=0, le=1_000_000)
    auto_accept: bool = True
    auto_fill_market: bool = False
    audit_max_records: int = Field(default=10_000, ge=1, le=1_000_000)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "broker_name": self.broker_name,
            "broker_account_id": self.broker_account_id,
            "simulation_seed": self.simulation_seed,
            "auto_accept": self.auto_accept,
            "auto_fill_market": self.auto_fill_market,
            "audit_max_records": self.audit_max_records,
        }
