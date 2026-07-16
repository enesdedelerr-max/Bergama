"""Order Management System domain and broker event contracts (#404)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.market_data.identity import InstrumentId
from app.market_data.timing import require_utc_aware
from app.orders.errors import OrderDecimalError
from app.orders.hashing import broker_event_identity, fill_event_identity
from app.orders.identity import OrderId
from app.orders.models import (
    BrokerLifecycleEventType,
    ExecutableOrder,
    OrderSide,
    OrderStatus,
)
from app.portfolio.decimal import (
    ZERO,
    parse_portfolio_decimal,
    quantize_money,
    quantize_price,
    quantize_quantity,
    require_non_negative,
    require_positive,
)
from app.portfolio.models import normalize_currency, validate_safe_metadata


class DomainEventType(StrEnum):
    ORDER_CREATED = "OrderCreated"
    ORDER_SUBMIT_REQUESTED = "OrderSubmitRequested"
    ORDER_SUBMITTED = "OrderSubmitted"
    ORDER_ACCEPTED = "OrderAccepted"
    ORDER_REJECTED = "OrderRejected"
    ORDER_PARTIALLY_FILLED = "OrderPartiallyFilled"
    ORDER_FILLED = "OrderFilled"
    CANCEL_REQUESTED = "CancelRequested"
    ORDER_CANCELLED = "OrderCancelled"
    ORDER_EXPIRED = "OrderExpired"
    BROKER_PORT_FAILED = "BrokerPortFailed"
    RECONCILIATION_REQUIRED = "ReconciliationRequired"


class BrokerCommandType(StrEnum):
    SUBMIT = "SUBMIT"
    CANCEL = "CANCEL"


class BrokerOrderCommand(BaseModel):
    """Description of broker work — aggregate never invokes the broker."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    command_type: BrokerCommandType
    order_id: OrderId
    executable_order: ExecutableOrder | None = None
    broker_order_id: str | None = Field(default=None, max_length=128)
    cancel_request_id: str | None = Field(default=None, max_length=128)
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)

    @model_validator(mode="after")
    def validate_payload(self) -> Self:
        if self.command_type is BrokerCommandType.SUBMIT and self.executable_order is None:
            msg = "SUBMIT requires executable_order"
            raise ValueError(msg)
        if self.command_type is BrokerCommandType.CANCEL and self.cancel_request_id is None:
            msg = "CANCEL requires cancel_request_id"
            raise ValueError(msg)
        return self


class BrokerOrderEvent(BaseModel):
    """Broker lifecycle event. Not a fill."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    broker_name: str = Field(min_length=1, max_length=64)
    broker_order_id: str = Field(min_length=1, max_length=128)
    broker_event_type: BrokerLifecycleEventType
    broker_event_sequence: int | None = Field(default=None, ge=0)
    broker_event_id: str | None = Field(default=None, max_length=128)
    event_identity: str | None = Field(default=None, min_length=64, max_length=64)
    reason_code: str | None = Field(default=None, max_length=96)
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
    safe_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("safe_metadata")
    @classmethod
    def metadata(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_safe_metadata(value)

    @model_validator(mode="after")
    def attach_identity(self) -> Self:
        identity = broker_event_identity(
            broker_name=self.broker_name,
            broker_order_id=self.broker_order_id,
            broker_event_type=self.broker_event_type.value,
            broker_event_sequence=self.broker_event_sequence,
            broker_event_id=self.broker_event_id,
        )
        if self.event_identity is None:
            object.__setattr__(self, "event_identity", identity)
        elif self.event_identity != identity:
            msg = "event_identity does not match deterministic broker identity"
            raise ValueError(msg)
        return self


class FillEvent(BaseModel):
    """Economic execution event. Never a broker lifecycle event."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fill_id: str | None = Field(default=None, max_length=128)
    broker_fill_id: str | None = Field(default=None, max_length=128)
    fill_identity: str | None = Field(default=None, min_length=64, max_length=64)
    order_id: OrderId
    broker_order_id: str | None = Field(default=None, max_length=128)
    instrument: InstrumentId
    side: OrderSide
    quantity: Decimal
    price: Decimal
    fee: Decimal = ZERO
    currency: str = Field(min_length=3, max_length=3)
    occurred_at: datetime
    known_at: datetime
    ingested_at: datetime
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
    idempotency_key: str = Field(min_length=1, max_length=512)
    safe_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("quantity", mode="before")
    @classmethod
    def parse_qty(cls, value: object) -> Decimal:
        try:
            return require_positive(
                quantize_quantity(parse_portfolio_decimal(value, field_name="quantity")),
                field_name="quantity",
            )
        except Exception as exc:
            raise OrderDecimalError(detail="quantity") from exc

    @field_validator("price", mode="before")
    @classmethod
    def parse_price(cls, value: object) -> Decimal:
        try:
            return require_positive(
                quantize_price(parse_portfolio_decimal(value, field_name="price")),
                field_name="price",
            )
        except Exception as exc:
            raise OrderDecimalError(detail="price") from exc

    @field_validator("fee", mode="before")
    @classmethod
    def parse_fee(cls, value: object) -> Decimal:
        try:
            return require_non_negative(
                quantize_money(parse_portfolio_decimal(value, field_name="fee")),
                field_name="fee",
            )
        except Exception as exc:
            raise OrderDecimalError(detail="fee") from exc

    @field_validator("currency")
    @classmethod
    def normalize_ccy(cls, value: str) -> str:
        return normalize_currency(value)

    @field_validator("occurred_at", "known_at", "ingested_at")
    @classmethod
    def utc_times(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="fill_timestamp")

    @field_validator("safe_metadata")
    @classmethod
    def metadata(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_safe_metadata(value)

    @model_validator(mode="after")
    def attach_identity_and_pit(self) -> Self:
        if self.fill_id is None and self.broker_fill_id is None:
            msg = "fill_id or broker_fill_id required"
            raise ValueError(msg)
        identity = fill_event_identity(fill_id=self.fill_id, broker_fill_id=self.broker_fill_id)
        if self.fill_identity is None:
            object.__setattr__(self, "fill_identity", identity)
        elif self.fill_identity != identity:
            msg = "fill_identity does not match deterministic fill identity"
            raise ValueError(msg)
        if self.known_at < self.occurred_at or self.ingested_at < self.known_at:
            msg = "fill timestamps must satisfy occurred_at <= known_at <= ingested_at"
            raise ValueError(msg)
        return self


class DomainEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_type: DomainEventType
    order_id: OrderId
    transition_id: str = Field(min_length=64, max_length=64)
    previous_status: OrderStatus | None = None
    next_status: OrderStatus
    previous_version: int = Field(ge=0)
    next_version: int = Field(ge=0)
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
    safe_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("safe_metadata")
    @classmethod
    def metadata(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_safe_metadata(value)
