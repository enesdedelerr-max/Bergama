"""OrderMutationResult — deterministic aggregate output (#404)."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.orders.audit import OrderAuditRecord
from app.orders.events import BrokerOrderCommand, DomainEvent, FillEvent
from app.orders.models import OrderMutationOutcome, OrderSnapshot


class OrderMutationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: OrderMutationOutcome
    duplicate: bool = False
    next_snapshot: OrderSnapshot
    broker_commands: tuple[BrokerOrderCommand, ...] = ()
    domain_events: tuple[DomainEvent, ...] = ()
    fill_events: tuple[FillEvent, ...] = ()
    audit_records: tuple[OrderAuditRecord, ...] = ()
    metrics: dict[str, int] = Field(default_factory=dict)
    transition_id: str | None = Field(default=None, min_length=64, max_length=64)
    idempotency_key: str = Field(min_length=1, max_length=512)

    @model_validator(mode="after")
    def validate_duplicate_flag(self) -> Self:
        if self.duplicate != (self.outcome is OrderMutationOutcome.DUPLICATE):
            msg = "duplicate must match DUPLICATE outcome"
            raise ValueError(msg)
        return self
