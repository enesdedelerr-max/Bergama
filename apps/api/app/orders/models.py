"""Order Management System domain models (#404)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.market_data.identity import InstrumentId
from app.market_data.timing import require_utc_aware
from app.orders.errors import OrderDecimalError
from app.orders.identity import ClientOrderId, OrderId
from app.portfolio.decimal import (
    ZERO,
    parse_portfolio_decimal,
    quantize_money,
    quantize_price,
    quantize_quantity,
    require_non_negative,
    require_positive,
)
from app.portfolio.identity import AccountId, PortfolioId
from app.portfolio.models import normalize_currency, validate_safe_metadata
from app.risk.models import TradeDirection


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class TimeInForce(StrEnum):
    DAY = "DAY"
    GTC = "GTC"


class OrderStatus(StrEnum):
    CREATED = "CREATED"
    PENDING_SUBMIT = "PENDING_SUBMIT"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCEL_PENDING = "CANCEL_PENDING"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


class OrderMutationOutcome(StrEnum):
    APPLIED = "APPLIED"
    DUPLICATE = "DUPLICATE"


class BrokerLifecycleEventType(StrEnum):
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    PORT_FAILED = "PORT_FAILED"


class OrderIntentReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    intent_id: str = Field(min_length=1, max_length=128)
    assessment_id: str = Field(min_length=64, max_length=64)
    assessment_hash: str = Field(min_length=64, max_length=64)
    policy_id: str = Field(min_length=1, max_length=128)
    policy_version: str = Field(min_length=1, max_length=32)
    policy_fingerprint: str = Field(min_length=64, max_length=64)
    portfolio_version: int = Field(ge=0)
    strategy_decision_id: str | None = Field(default=None, max_length=128)
    strategy_action: str | None = Field(default=None, max_length=64)
    strategy_run_id: str | None = Field(default=None, max_length=128)

    @field_validator("assessment_id", "assessment_hash", "policy_fingerprint")
    @classmethod
    def sha256_hex(cls, value: str) -> str:
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "hash fields must be sha256 hex"
            raise ValueError(msg)
        return text


class ExecutableOrder(BaseModel):
    """Immutable broker-facing domain contract. No provider SDK types."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    order_id: OrderId
    client_order_id: ClientOrderId
    account_id: AccountId
    portfolio_id: PortfolioId
    instrument: InstrumentId
    side: OrderSide
    quantity: Decimal
    order_type: OrderType
    time_in_force: TimeInForce
    limit_price: Decimal | None = None
    currency: str = Field(min_length=3, max_length=3)
    reference_price: Decimal
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)

    @field_validator("quantity", mode="before")
    @classmethod
    def parse_quantity(cls, value: object) -> Decimal:
        try:
            return require_positive(
                quantize_quantity(parse_portfolio_decimal(value, field_name="quantity")),
                field_name="quantity",
            )
        except Exception as exc:
            raise OrderDecimalError(detail="quantity") from exc

    @field_validator("limit_price", "reference_price", mode="before")
    @classmethod
    def parse_prices(cls, value: object) -> Decimal | None:
        if value is None:
            return None
        try:
            return require_positive(
                quantize_price(parse_portfolio_decimal(value, field_name="price")),
                field_name="price",
            )
        except Exception as exc:
            raise OrderDecimalError(detail="price") from exc

    @field_validator("currency")
    @classmethod
    def normalize_ccy(cls, value: str) -> str:
        return normalize_currency(value)

    @model_validator(mode="after")
    def validate_limit(self) -> Self:
        if self.order_type is OrderType.LIMIT and self.limit_price is None:
            msg = "LIMIT orders require limit_price"
            raise ValueError(msg)
        if self.order_type is OrderType.MARKET and self.limit_price is not None:
            msg = "MARKET orders must not include limit_price"
            raise ValueError(msg)
        return self


class FillRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fill_identity: str = Field(min_length=64, max_length=64)
    fill_id: str | None = Field(default=None, max_length=128)
    broker_fill_id: str | None = Field(default=None, max_length=128)
    quantity: Decimal
    price: Decimal
    fee: Decimal = ZERO
    occurred_at: datetime

    @field_validator("quantity", mode="before")
    @classmethod
    def positive_qty(cls, value: object) -> Decimal:
        try:
            return require_positive(
                quantize_quantity(parse_portfolio_decimal(value, field_name="quantity")),
                field_name="quantity",
            )
        except Exception as exc:
            raise OrderDecimalError(detail="quantity") from exc

    @field_validator("price", mode="before")
    @classmethod
    def positive_price(cls, value: object) -> Decimal:
        try:
            return require_positive(
                quantize_price(parse_portfolio_decimal(value, field_name="price")),
                field_name="price",
            )
        except Exception as exc:
            raise OrderDecimalError(detail="price") from exc

    @field_validator("fee", mode="before")
    @classmethod
    def non_neg_fee(cls, value: object) -> Decimal:
        try:
            return require_non_negative(
                quantize_money(parse_portfolio_decimal(value, field_name="fee")),
                field_name="fee",
            )
        except Exception as exc:
            raise OrderDecimalError(detail="fee") from exc

    @field_validator("occurred_at")
    @classmethod
    def utc_time(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="occurred_at")


class OrderSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    order_id: OrderId
    client_order_id: ClientOrderId
    account_id: AccountId
    portfolio_id: PortfolioId
    instrument: InstrumentId
    side: OrderSide
    quantity: Decimal
    order_type: OrderType
    time_in_force: TimeInForce
    limit_price: Decimal | None = None
    currency: str = Field(min_length=3, max_length=3)
    reference_price: Decimal
    status: OrderStatus
    order_version: int = Field(ge=0)
    intent_reference: OrderIntentReference
    broker_order_id: str | None = Field(default=None, max_length=128)
    cumulative_filled_quantity: Decimal = ZERO
    remaining_quantity: Decimal
    average_fill_price: Decimal | None = None
    total_fees: Decimal = ZERO
    fills: tuple[FillRecord, ...] = ()
    seen_broker_event_identities: tuple[str, ...] = ()
    seen_fill_identities: tuple[str, ...] = ()
    last_broker_event_sequence: int | None = None
    last_transition_id: str | None = Field(default=None, min_length=64, max_length=64)
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
    safe_metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @field_validator("quantity", "remaining_quantity", "cumulative_filled_quantity", mode="before")
    @classmethod
    def parse_qty(cls, value: object) -> Decimal:
        try:
            return quantize_quantity(parse_portfolio_decimal(value, field_name="quantity"))
        except Exception as exc:
            raise OrderDecimalError(detail="quantity") from exc

    @field_validator("reference_price", "limit_price", "average_fill_price", mode="before")
    @classmethod
    def parse_optional_price(cls, value: object) -> Decimal | None:
        if value is None:
            return None
        try:
            return require_positive(
                quantize_price(parse_portfolio_decimal(value, field_name="price")),
                field_name="price",
            )
        except Exception as exc:
            raise OrderDecimalError(detail="price") from exc

    @field_validator("total_fees", mode="before")
    @classmethod
    def parse_fees(cls, value: object) -> Decimal:
        try:
            return require_non_negative(
                quantize_money(parse_portfolio_decimal(value, field_name="total_fees")),
                field_name="total_fees",
            )
        except Exception as exc:
            raise OrderDecimalError(detail="total_fees") from exc

    @field_validator("currency")
    @classmethod
    def normalize_ccy(cls, value: str) -> str:
        return normalize_currency(value)

    @field_validator("created_at", "updated_at")
    @classmethod
    def utc_times(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="order_timestamp")

    @field_validator("safe_metadata")
    @classmethod
    def metadata(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_safe_metadata(value)

    @model_validator(mode="after")
    def validate_quantities(self) -> Self:
        if self.remaining_quantity < ZERO or self.cumulative_filled_quantity < ZERO:
            msg = "fill quantities must be non-negative"
            raise ValueError(msg)
        if self.cumulative_filled_quantity + self.remaining_quantity != self.quantity:
            msg = "cumulative + remaining must equal order quantity"
            raise ValueError(msg)
        return self


def side_from_intent(direction: TradeDirection | None, quantity_delta: Decimal) -> OrderSide:
    if direction is TradeDirection.BUY:
        return OrderSide.BUY
    if direction is TradeDirection.SELL:
        return OrderSide.SELL
    return OrderSide.BUY if quantity_delta > ZERO else OrderSide.SELL


def absolute_quantity(quantity_delta: Decimal) -> Decimal:
    return quantize_quantity(abs(quantity_delta))
