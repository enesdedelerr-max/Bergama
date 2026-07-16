"""Payload-safe Order Management System audit models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.market_data.timing import require_utc_aware
from app.orders.identity import OrderId
from app.orders.models import OrderMutationOutcome, OrderStatus


class OrderAuditRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    order_id: OrderId
    previous_version: int = Field(ge=0)
    next_version: int = Field(ge=0)
    previous_status: OrderStatus | None = None
    next_status: OrderStatus
    transition_id: str | None = Field(default=None, min_length=64, max_length=64)
    command_or_event_key: str = Field(min_length=1, max_length=512)
    assessment_id: str | None = Field(default=None, max_length=64)
    broker_event_identity: str | None = Field(default=None, max_length=64)
    outcome: OrderMutationOutcome
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
    recorded_at: datetime
    error_code: str | None = Field(default=None, max_length=96)

    @field_validator("recorded_at")
    @classmethod
    def utc_recorded_at(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="recorded_at")


class InMemoryOrderAuditSink:
    def __init__(self, *, max_records: int = 10_000) -> None:
        self._max_records = max_records
        self._records: list[OrderAuditRecord] = []

    def record(self, record: OrderAuditRecord) -> None:
        self._records.append(record)
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records :]

    @property
    def records(self) -> tuple[OrderAuditRecord, ...]:
        return tuple(self._records)
