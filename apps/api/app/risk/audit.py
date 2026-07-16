"""Payload-safe Risk Engine audit models and in-memory sink."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.market_data.timing import require_utc_aware
from app.portfolio.identity import PortfolioId
from app.risk.models import RiskFinalAction


class RiskAuditRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    assessment_id: str = Field(min_length=64, max_length=64)
    intent_id: str = Field(min_length=1, max_length=128)
    portfolio_id: PortfolioId
    portfolio_version: int = Field(ge=0)
    final_action: RiskFinalAction
    policy_fingerprint: str = Field(min_length=64, max_length=64)
    recorded_at: datetime
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
    error_code: str | None = Field(default=None, max_length=96)

    @field_validator("recorded_at")
    @classmethod
    def utc_recorded_at(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="recorded_at")


class InMemoryRiskAuditSink:
    def __init__(self, *, max_records: int = 1000) -> None:
        self._max_records = max_records
        self._records: list[RiskAuditRecord] = []

    def record(self, record: RiskAuditRecord) -> None:
        self._records.append(record)
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records :]

    @property
    def records(self) -> tuple[RiskAuditRecord, ...]:
        return tuple(self._records)
