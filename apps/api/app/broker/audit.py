"""Payload-safe broker audit records (#405)."""

from __future__ import annotations

from collections import deque
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.broker.outcomes import BrokerCommandOutcome
from app.orders.identity import OrderId
from app.portfolio.models import validate_safe_metadata


class BrokerAuditRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    order_id: OrderId | None = None
    command_kind: str = Field(min_length=1, max_length=32)
    outcome: BrokerCommandOutcome | None = None
    submission_identity: str | None = Field(default=None, min_length=64, max_length=64)
    broker_order_id: str | None = Field(default=None, max_length=128)
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
    recorded_at: datetime
    reason_code: str | None = Field(default=None, max_length=96)
    safe_metadata: dict[str, str] = Field(default_factory=dict)

    @classmethod
    def clean_metadata(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_safe_metadata(value)


class InMemoryBrokerAuditSink:
    def __init__(self, *, max_records: int = 10_000) -> None:
        self._max = max_records
        self._records: deque[BrokerAuditRecord] = deque(maxlen=max_records)

    def record(self, record: BrokerAuditRecord) -> None:
        self._records.append(record)

    @property
    def records(self) -> tuple[BrokerAuditRecord, ...]:
        return tuple(self._records)

    def clear(self) -> None:
        self._records.clear()
