"""Portfolio Aggregate domain models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.market_data.identity import InstrumentId
from app.market_data.quality import DataQualityFlags
from app.market_data.timing import require_utc_aware, validate_point_in_time_order
from app.portfolio.decimal import (
    ZERO,
    parse_portfolio_decimal,
    quantize_money,
    quantize_pnl,
    quantize_price,
    quantize_quantity,
    require_non_negative,
    require_positive,
)
from app.portfolio.identity import AccountId, PortfolioId

_SENSITIVE_TOKENS = ("password", "secret", "token", "api_key", "apikey", "authorization")


class FillSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class PortfolioMutationType(StrEnum):
    CREATE_PORTFOLIO = "CREATE_PORTFOLIO"
    FILL_APPLIED = "FILL_APPLIED"
    CASH_ADJUSTMENT = "CASH_ADJUSTMENT"
    MARK_PRICE_UPDATE = "MARK_PRICE_UPDATE"


class CashAdjustmentReason(StrEnum):
    INITIAL_FUNDING = "initial_funding"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    FEE_CORRECTION = "fee_correction"
    CASH_CORRECTION = "cash_correction"


class PortfolioMutationOutcome(StrEnum):
    APPLIED = "APPLIED"
    DUPLICATE = "DUPLICATE"


class PortfolioProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    order_reference: str | None = Field(default=None, max_length=128)
    strategy_decision_id: str | None = Field(default=None, max_length=128)
    strategy_allocation_id: str | None = Field(default=None, max_length=128)

    @field_validator("order_reference", "strategy_decision_id", "strategy_allocation_id")
    @classmethod
    def clean_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        return text or None


class PortfolioInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str = Field(min_length=1, max_length=128)
    idempotency_key: str = Field(min_length=1, max_length=512)
    account_id: AccountId
    portfolio_id: PortfolioId
    occurred_at: datetime
    known_at: datetime
    ingested_at: datetime
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
    safe_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("occurred_at", "known_at", "ingested_at")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="portfolio_timestamp")

    @field_validator("event_id", "idempotency_key", "correlation_id", "causation_id")
    @classmethod
    def clean_optional_tokens(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if not text:
            msg = "identifier fields must be non-empty when provided"
            raise ValueError(msg)
        return text

    @field_validator("safe_metadata")
    @classmethod
    def safe_metadata_only(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_safe_metadata(value)

    @model_validator(mode="after")
    def validate_pit(self) -> Self:
        validate_point_in_time_order(
            occurred_at=self.occurred_at,
            effective_at=self.occurred_at,
            known_at=self.known_at,
            ingested_at=self.ingested_at,
            quality=DataQualityFlags(),
        )
        return self


class FillApplied(PortfolioInput):
    fill_id: str = Field(min_length=1, max_length=128)
    instrument: InstrumentId
    side: FillSide
    quantity: Decimal
    price: Decimal
    currency: str = Field(min_length=3, max_length=3)
    fee: Decimal = Field(default=ZERO)
    provenance: PortfolioProvenance = Field(default_factory=PortfolioProvenance)

    @field_validator("fill_id")
    @classmethod
    def clean_fill_id(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "fill_id must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator("quantity", mode="before")
    @classmethod
    def parse_quantity(cls, value: object) -> Decimal:
        return require_positive(
            quantize_quantity(parse_portfolio_decimal(value, field_name="quantity")),
            field_name="quantity",
        )

    @field_validator("price", mode="before")
    @classmethod
    def parse_price(cls, value: object) -> Decimal:
        return require_positive(
            quantize_price(parse_portfolio_decimal(value, field_name="price")),
            field_name="price",
        )

    @field_validator("fee", mode="before")
    @classmethod
    def parse_fee(cls, value: object) -> Decimal:
        return require_non_negative(
            quantize_money(parse_portfolio_decimal(value, field_name="fee")),
            field_name="fee",
        )

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return normalize_currency(value)


class CashAdjustment(PortfolioInput):
    amount: Decimal
    currency: str = Field(min_length=3, max_length=3)
    reason: CashAdjustmentReason

    @field_validator("amount", mode="before")
    @classmethod
    def parse_amount(cls, value: object) -> Decimal:
        return quantize_money(parse_portfolio_decimal(value, field_name="amount"))

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return normalize_currency(value)


class MarkPriceUpdate(PortfolioInput):
    instrument: InstrumentId
    mark_price: Decimal
    currency: str = Field(min_length=3, max_length=3)
    mark_time: datetime

    @field_validator("mark_price", mode="before")
    @classmethod
    def parse_mark_price(cls, value: object) -> Decimal:
        return require_positive(
            quantize_price(parse_portfolio_decimal(value, field_name="mark_price")),
            field_name="mark_price",
        )

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return normalize_currency(value)

    @field_validator("mark_time")
    @classmethod
    def utc_mark_time(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="mark_time")


class CashState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    currency: str = Field(min_length=3, max_length=3)
    cash_balance: Decimal = ZERO
    realized_pnl: Decimal = ZERO
    fees_total: Decimal = ZERO

    @field_validator("currency")
    @classmethod
    def cash_currency(cls, value: str) -> str:
        return normalize_currency(value)

    @field_validator("cash_balance", "realized_pnl", "fees_total", mode="before")
    @classmethod
    def parse_money(cls, value: object) -> Decimal:
        return quantize_money(parse_portfolio_decimal(value, field_name="cash_state"))


class PositionState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    instrument: InstrumentId
    currency: str = Field(min_length=3, max_length=3)
    quantity: Decimal = ZERO
    average_cost: Decimal = ZERO
    last_mark_price: Decimal | None = None
    last_mark_at: datetime | None = None
    market_value: Decimal = ZERO
    unrealized_pnl: Decimal = ZERO

    @field_validator("currency")
    @classmethod
    def position_currency(cls, value: str) -> str:
        return normalize_currency(value)

    @field_validator("quantity", mode="before")
    @classmethod
    def position_quantity(cls, value: object) -> Decimal:
        return quantize_quantity(parse_portfolio_decimal(value, field_name="quantity"))

    @field_validator("average_cost", "market_value", mode="before")
    @classmethod
    def positive_or_zero_money(cls, value: object) -> Decimal:
        parsed = quantize_money(parse_portfolio_decimal(value, field_name="position_money"))
        return require_non_negative(parsed, field_name="position_money")

    @field_validator("unrealized_pnl", mode="before")
    @classmethod
    def pnl_value(cls, value: object) -> Decimal:
        return quantize_pnl(parse_portfolio_decimal(value, field_name="unrealized_pnl"))

    @field_validator("last_mark_price", mode="before")
    @classmethod
    def optional_mark_price(cls, value: object) -> Decimal | None:
        if value is None:
            return None
        return require_positive(
            quantize_price(parse_portfolio_decimal(value, field_name="last_mark_price")),
            field_name="last_mark_price",
        )

    @field_validator("last_mark_at")
    @classmethod
    def optional_mark_time(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return require_utc_aware(value, field_name="last_mark_at")

    @property
    def instrument_key(self) -> str:
        return self.instrument.instrument_key


class CashDelta(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    currency: str = Field(min_length=3, max_length=3)
    amount: Decimal = ZERO

    @field_validator("currency")
    @classmethod
    def delta_currency(cls, value: str) -> str:
        return normalize_currency(value)

    @field_validator("amount", mode="before")
    @classmethod
    def delta_amount(cls, value: object) -> Decimal:
        return quantize_money(parse_portfolio_decimal(value, field_name="cash_delta"))


class PositionDelta(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    instrument: InstrumentId | None = None
    quantity_delta: Decimal = ZERO
    opened: bool = False
    closed: bool = False
    reversed: bool = False

    @field_validator("quantity_delta", mode="before")
    @classmethod
    def parse_quantity_delta(cls, value: object) -> Decimal:
        return quantize_quantity(parse_portfolio_decimal(value, field_name="quantity_delta"))


class PortfolioSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    account_id: AccountId
    portfolio_id: PortfolioId
    base_currency: str = Field(min_length=3, max_length=3)
    cash: CashState
    positions: tuple[PositionState, ...] = ()
    realized_pnl: Decimal = ZERO
    unrealized_pnl: Decimal = ZERO
    fees_total: Decimal = ZERO
    market_value: Decimal = ZERO
    gross_exposure: Decimal = ZERO
    net_exposure: Decimal = ZERO
    portfolio_version: int = Field(ge=0)
    last_applied_event_key: str | None = Field(default=None, max_length=512)
    configuration_fingerprint: str = Field(min_length=64, max_length=64)
    snapshot_at: datetime
    snapshot_hash: str | None = Field(default=None, min_length=64, max_length=64)
    safe_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("base_currency")
    @classmethod
    def snapshot_currency(cls, value: str) -> str:
        return normalize_currency(value)

    @field_validator(
        "realized_pnl",
        "unrealized_pnl",
        "fees_total",
        "market_value",
        "gross_exposure",
        "net_exposure",
        mode="before",
    )
    @classmethod
    def parse_snapshot_money(cls, value: object) -> Decimal:
        return quantize_money(parse_portfolio_decimal(value, field_name="snapshot_money"))

    @field_validator("snapshot_at")
    @classmethod
    def utc_snapshot_at(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="snapshot_at")

    @field_validator("configuration_fingerprint", "snapshot_hash")
    @classmethod
    def sha256_or_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "hash fields must be sha256 hex"
            raise ValueError(msg)
        return text

    @field_validator("safe_metadata")
    @classmethod
    def snapshot_metadata(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_safe_metadata(value)

    @model_validator(mode="after")
    def validate_snapshot(self) -> Self:
        ordered = tuple(sorted(self.positions, key=lambda p: p.instrument.instrument_key))
        if self.positions != ordered:
            msg = "positions must be sorted by instrument_key"
            raise ValueError(msg)
        if self.cash.currency != self.base_currency:
            msg = "cash currency must equal base_currency"
            raise ValueError(msg)
        for position in self.positions:
            if position.currency != self.base_currency:
                msg = "position currency must equal base_currency"
                raise ValueError(msg)
        return self


class LedgerEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ledger_entry_id: str = Field(min_length=64, max_length=64)
    ledger_version: int = Field(ge=1)
    portfolio_version: int = Field(ge=1)
    mutation_type: PortfolioMutationType
    source_event_id: str = Field(min_length=1, max_length=128)
    idempotency_key: str = Field(min_length=1, max_length=512)
    instrument: InstrumentId | None = None
    cash_delta: CashDelta
    quantity_delta: Decimal = ZERO
    realized_pnl_delta: Decimal = ZERO
    fee: Decimal = ZERO
    occurred_at: datetime
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
    provenance: PortfolioProvenance = Field(default_factory=PortfolioProvenance)
    safe_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("ledger_entry_id")
    @classmethod
    def ledger_hash(cls, value: str) -> str:
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "ledger_entry_id must be sha256 hex"
            raise ValueError(msg)
        return text

    @field_validator("quantity_delta", mode="before")
    @classmethod
    def ledger_quantity(cls, value: object) -> Decimal:
        return quantize_quantity(parse_portfolio_decimal(value, field_name="quantity_delta"))

    @field_validator("realized_pnl_delta", mode="before")
    @classmethod
    def ledger_pnl(cls, value: object) -> Decimal:
        return quantize_pnl(parse_portfolio_decimal(value, field_name="realized_pnl_delta"))

    @field_validator("fee", mode="before")
    @classmethod
    def ledger_fee(cls, value: object) -> Decimal:
        return require_non_negative(
            quantize_money(parse_portfolio_decimal(value, field_name="fee")),
            field_name="fee",
        )

    @field_validator("occurred_at")
    @classmethod
    def ledger_time(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="occurred_at")

    @field_validator("safe_metadata")
    @classmethod
    def ledger_metadata(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_safe_metadata(value)


class PortfolioMutationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: PortfolioMutationOutcome
    duplicate: bool = False
    mutation_type: PortfolioMutationType
    next_snapshot: PortfolioSnapshot
    ledger_entries: tuple[LedgerEntry, ...] = ()
    realized_pnl_delta: Decimal = ZERO
    cash_delta: CashDelta
    position_delta: PositionDelta
    idempotency_key: str = Field(min_length=1, max_length=512)
    duplicate_of_version: int | None = Field(default=None, ge=0)

    @field_validator("realized_pnl_delta", mode="before")
    @classmethod
    def result_pnl(cls, value: object) -> Decimal:
        return quantize_pnl(parse_portfolio_decimal(value, field_name="realized_pnl_delta"))

    @model_validator(mode="after")
    def validate_duplicate_outcome(self) -> Self:
        if self.duplicate != (self.outcome is PortfolioMutationOutcome.DUPLICATE):
            msg = "duplicate must match DUPLICATE outcome"
            raise ValueError(msg)
        return self


class FillAppliedCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mutation: FillApplied
    expected_version: int = Field(ge=0)


class CashAdjustmentCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mutation: CashAdjustment
    expected_version: int = Field(ge=0)


class MarkPriceUpdateCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mutation: MarkPriceUpdate
    expected_version: int = Field(ge=0)


def normalize_currency(value: str) -> str:
    text = value.strip().upper()
    if len(text) != 3 or not text.isalpha():
        msg = "currency must be a 3-letter ISO code"
        raise ValueError(msg)
    return text


def validate_safe_metadata(value: dict[str, str]) -> dict[str, str]:
    if len(value) > 16:
        msg = "safe_metadata may contain at most 16 entries"
        raise ValueError(msg)
    cleaned: dict[str, str] = {}
    for key, raw in value.items():
        k = str(key).strip()
        v = str(raw).strip()
        if not k or len(k) > 64 or len(v) > 256:
            msg = "safe_metadata keys/values exceed allowed bounds"
            raise ValueError(msg)
        if any(token in k.lower() for token in _SENSITIVE_TOKENS):
            msg = f"forbidden safe_metadata key {k!r}"
            raise ValueError(msg)
        cleaned[k] = v
    return cleaned
