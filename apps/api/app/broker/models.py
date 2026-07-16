"""Broker domain models — commands, events, results (#405).

Broker adapters emit typed facts only. They never own OMS transitions/versions.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.broker.hashing import build_broker_event_identity, build_broker_fill_identity
from app.broker.identity import BrokerAccountId, BrokerName
from app.broker.metadata import normalize_provider_metadata
from app.broker.outcomes import BrokerCommandOutcome
from app.market_data.identity import InstrumentId
from app.market_data.timing import require_utc_aware
from app.orders.errors import OrderDecimalError
from app.orders.identity import ClientOrderId, OrderId
from app.orders.models import ExecutableOrder, OrderSide
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


class BrokerLifecycleEventType(StrEnum):
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    CONNECTION_LOST = "CONNECTION_LOST"
    OUTCOME_UNKNOWN = "OUTCOME_UNKNOWN"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


class SubmitExecutableOrder(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    executable_order: ExecutableOrder
    idempotency_key: str = Field(min_length=1, max_length=512)
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)

    @field_validator("idempotency_key", "correlation_id", "causation_id")
    @classmethod
    def clean_tokens(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if not text:
            msg = "identifier fields must be non-empty when provided"
            raise ValueError(msg)
        return text


class CancelExecutableOrder(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    order_id: OrderId
    client_order_id: ClientOrderId | None = None
    broker_order_id: str | None = Field(default=None, max_length=128)
    cancel_request_id: str = Field(min_length=1, max_length=128)
    idempotency_key: str = Field(min_length=1, max_length=512)
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)

    @field_validator("cancel_request_id", "idempotency_key", "correlation_id", "causation_id")
    @classmethod
    def clean_tokens(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if not text:
            msg = "identifier fields must be non-empty when provided"
            raise ValueError(msg)
        return text


class BrokerLifecycleEvent(BaseModel):
    """Normalized broker lifecycle fact. Never a fill. Never a provider DTO."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    broker_name: BrokerName
    broker_account_id: BrokerAccountId
    broker_order_id: str = Field(min_length=1, max_length=128)
    broker_event_type: BrokerLifecycleEventType
    broker_sequence: int | None = Field(default=None, ge=0)
    broker_event_id: str | None = Field(default=None, max_length=128)
    event_identity: str | None = Field(default=None, min_length=64, max_length=64)
    order_id: OrderId | None = None
    client_order_id: ClientOrderId | None = None
    reason_code: str | None = Field(default=None, max_length=96)
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
    occurred_at: datetime | None = None
    received_at: datetime | None = None
    safe_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("occurred_at", "received_at")
    @classmethod
    def utc_times(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return require_utc_aware(value, field_name="broker_timestamp")

    @field_validator("safe_metadata")
    @classmethod
    def metadata(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_safe_metadata(value)

    @model_validator(mode="after")
    def attach_identity(self) -> Self:
        identity = build_broker_event_identity(
            broker_name=self.broker_name.value,
            broker_order_id=self.broker_order_id,
            broker_event_type=self.broker_event_type.value,
            broker_sequence=self.broker_sequence,
            broker_event_id=self.broker_event_id,
        )
        if self.event_identity is None:
            object.__setattr__(self, "event_identity", identity)
        elif self.event_identity != identity:
            msg = "event_identity does not match deterministic broker identity"
            raise ValueError(msg)
        return self


class BrokerFillEvent(BaseModel):
    """Normalized economic fill fact. Never a lifecycle acknowledgement."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    broker_name: BrokerName
    broker_account_id: BrokerAccountId
    broker_order_id: str = Field(min_length=1, max_length=128)
    broker_fill_id: str | None = Field(default=None, max_length=128)
    fill_id: str | None = Field(default=None, max_length=128)
    fill_identity: str | None = Field(default=None, min_length=64, max_length=64)
    order_id: OrderId
    instrument: InstrumentId
    side: OrderSide
    quantity: Decimal
    price: Decimal
    fee: Decimal = ZERO
    currency: str = Field(min_length=3, max_length=3)
    occurred_at: datetime
    received_at: datetime | None = None
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
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

    @field_validator("occurred_at", "received_at")
    @classmethod
    def utc_times(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return require_utc_aware(value, field_name="fill_timestamp")

    @field_validator("safe_metadata")
    @classmethod
    def metadata(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_safe_metadata(value)

    @model_validator(mode="after")
    def attach_identity(self) -> Self:
        if self.broker_fill_id is None and self.fill_id is None:
            msg = "broker_fill_id or fill_id required"
            raise ValueError(msg)
        identity = build_broker_fill_identity(
            broker_fill_id=self.broker_fill_id,
            fill_id=self.fill_id,
        )
        if self.fill_identity is None:
            object.__setattr__(self, "fill_identity", identity)
        elif self.fill_identity != identity:
            msg = "fill_identity does not match deterministic fill identity"
            raise ValueError(msg)
        return self


class BrokerSubmissionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: BrokerCommandOutcome
    submission_identity: str = Field(min_length=64, max_length=64)
    broker_order_id: str | None = Field(default=None, max_length=128)
    lifecycle_events: tuple[BrokerLifecycleEvent, ...] = ()
    fill_events: tuple[BrokerFillEvent, ...] = ()
    reason_code: str | None = Field(default=None, max_length=96)
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
    safe_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("safe_metadata")
    @classmethod
    def metadata(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_safe_metadata(value)


class BrokerCancelResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: BrokerCommandOutcome
    broker_order_id: str | None = Field(default=None, max_length=128)
    lifecycle_events: tuple[BrokerLifecycleEvent, ...] = ()
    reason_code: str | None = Field(default=None, max_length=96)
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
    safe_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("safe_metadata")
    @classmethod
    def metadata(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_safe_metadata(value)


def normalize_raw_metadata(raw: dict[str, object] | None) -> dict[str, str]:
    return normalize_provider_metadata(raw)
