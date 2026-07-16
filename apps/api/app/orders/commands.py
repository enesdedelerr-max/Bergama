"""Order Management System commands (#404)."""

from __future__ import annotations

from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.orders.errors import OrderDecimalError
from app.orders.events import BrokerOrderEvent, FillEvent
from app.orders.identity import ClientOrderId, OrderId
from app.orders.models import OrderType, TimeInForce
from app.portfolio.decimal import parse_portfolio_decimal, quantize_price, require_positive
from app.portfolio.models import validate_safe_metadata
from app.risk.models import ProposedTradeIntent, RiskAssessment


class SubmitOrder(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    intent: ProposedTradeIntent
    assessment: RiskAssessment
    client_order_id: ClientOrderId
    order_type: OrderType
    time_in_force: TimeInForce
    limit_price: Decimal | None = None
    idempotency_key: str = Field(min_length=1, max_length=512)
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
    safe_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("limit_price", mode="before")
    @classmethod
    def parse_limit(cls, value: object) -> Decimal | None:
        if value is None:
            return None
        try:
            return require_positive(
                quantize_price(parse_portfolio_decimal(value, field_name="limit_price")),
                field_name="limit_price",
            )
        except Exception as exc:
            raise OrderDecimalError(detail="limit_price") from exc

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

    @field_validator("safe_metadata")
    @classmethod
    def metadata(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_safe_metadata(value)

    @model_validator(mode="after")
    def validate_order_type_price(self) -> Self:
        if self.order_type is OrderType.LIMIT and self.limit_price is None:
            msg = "LIMIT submit requires limit_price"
            raise ValueError(msg)
        if self.order_type is OrderType.MARKET and self.limit_price is not None:
            msg = "MARKET submit must not include limit_price"
            raise ValueError(msg)
        return self


class RequestCancel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    order_id: OrderId
    cancel_request_id: str = Field(min_length=1, max_length=128)
    expected_version: int = Field(ge=0)
    idempotency_key: str = Field(min_length=1, max_length=512)
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
    safe_metadata: dict[str, str] = Field(default_factory=dict)

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

    @field_validator("safe_metadata")
    @classmethod
    def metadata(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_safe_metadata(value)


class ApplyBrokerEvent(BaseModel):
    """Apply either a broker lifecycle event or an economic fill — never both."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    order_id: OrderId
    expected_version: int = Field(ge=0)
    broker_event: BrokerOrderEvent | None = None
    fill_event: FillEvent | None = None
    idempotency_key: str = Field(min_length=1, max_length=512)

    @model_validator(mode="after")
    def exactly_one_payload(self) -> Self:
        has_broker = self.broker_event is not None
        has_fill = self.fill_event is not None
        if has_broker == has_fill:
            msg = "provide exactly one of broker_event or fill_event"
            raise ValueError(msg)
        return self
