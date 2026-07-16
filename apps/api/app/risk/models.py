"""Risk Engine domain models.

Pure evaluation contracts only. No orders, sizing, or portfolio mutation.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.market_data.identity import InstrumentId
from app.market_data.timing import require_utc_aware
from app.portfolio.decimal import (
    ZERO,
    parse_portfolio_decimal,
    quantize_price,
    quantize_quantity,
    require_positive,
)
from app.portfolio.identity import AccountId, PortfolioId
from app.portfolio.models import normalize_currency, validate_safe_metadata
from app.risk.errors import RiskDecimalError
from app.strategy.models import StrategyAction


class TradeDirection(StrEnum):
    BUY = "buy"
    SELL = "sell"


class RiskRuleId(StrEnum):
    INTENT_INVALID = "risk.intent_invalid"
    POLICY_CURRENCY_MISMATCH = "risk.policy_currency_mismatch"
    PORTFOLIO_VERSION_MISMATCH = "risk.portfolio_version_mismatch"
    KILL_SWITCH = "risk.kill_switch"
    SNAPSHOT_STALE = "risk.snapshot_stale"
    MARK_STALE = "risk.mark_stale"
    SHORTING_DISABLED = "risk.shorting_disabled"
    ORDER_NOTIONAL_LIMIT = "risk.order_notional_limit"
    POSITION_NOTIONAL_LIMIT = "risk.position_notional_limit"
    GROSS_EXPOSURE_LIMIT = "risk.gross_exposure_limit"
    NET_EXPOSURE_LIMIT = "risk.net_exposure_limit"
    CONCENTRATION_LIMIT = "risk.concentration_limit"


class RiskRuleStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"


class RiskSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class RiskFinalAction(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    HALT = "HALT"


class ProposedTradeIntent(BaseModel):
    """Sized trade proposal. Quantity must come from here, never StrategyDecision."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    intent_id: str = Field(min_length=1, max_length=128)
    portfolio_id: PortfolioId
    account_id: AccountId
    instrument_id: InstrumentId
    quantity_delta: Decimal | None = None
    quantity: Decimal | None = None
    direction: TradeDirection | None = None
    reference_price: Decimal
    currency: str = Field(min_length=3, max_length=3)
    expected_portfolio_version: int = Field(ge=0)
    strategy_decision_id: str | None = Field(default=None, max_length=128)
    strategy_action: StrategyAction | None = None
    strategy_run_id: str | None = Field(default=None, max_length=128)
    occurred_at: datetime
    known_at: datetime
    submitted_at: datetime
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
    safe_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator(
        "intent_id",
        "strategy_decision_id",
        "strategy_run_id",
        "correlation_id",
        "causation_id",
    )
    @classmethod
    def clean_optional_tokens(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if not text:
            msg = "identifier fields must be non-empty when provided"
            raise ValueError(msg)
        return text

    @field_validator("quantity_delta", mode="before")
    @classmethod
    def parse_quantity_delta(cls, value: object) -> Decimal | None:
        if value is None:
            return None
        try:
            return quantize_quantity(parse_portfolio_decimal(value, field_name="quantity_delta"))
        except Exception as exc:
            raise RiskDecimalError(detail="quantity_delta") from exc

    @field_validator("quantity", mode="before")
    @classmethod
    def parse_quantity(cls, value: object) -> Decimal | None:
        if value is None:
            return None
        try:
            return require_positive(
                quantize_quantity(parse_portfolio_decimal(value, field_name="quantity")),
                field_name="quantity",
            )
        except Exception as exc:
            raise RiskDecimalError(detail="quantity") from exc

    @field_validator("reference_price", mode="before")
    @classmethod
    def parse_reference_price(cls, value: object) -> Decimal:
        try:
            return require_positive(
                quantize_price(parse_portfolio_decimal(value, field_name="reference_price")),
                field_name="reference_price",
            )
        except Exception as exc:
            raise RiskDecimalError(detail="reference_price") from exc

    @field_validator("currency")
    @classmethod
    def normalize_intent_currency(cls, value: str) -> str:
        return normalize_currency(value)

    @field_validator("occurred_at", "known_at", "submitted_at")
    @classmethod
    def utc_timestamps(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="intent_timestamp")

    @field_validator("safe_metadata")
    @classmethod
    def safe_metadata_only(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_safe_metadata(value)

    @model_validator(mode="after")
    def normalize_quantity_representation(self) -> Self:
        has_delta = self.quantity_delta is not None
        has_signed_pair = self.quantity is not None and self.direction is not None
        if has_delta == has_signed_pair:
            msg = "provide exactly one of quantity_delta or (quantity + direction)"
            raise ValueError(msg)
        if has_signed_pair:
            assert self.quantity is not None and self.direction is not None
            signed = self.quantity if self.direction is TradeDirection.BUY else -self.quantity
            object.__setattr__(self, "quantity_delta", quantize_quantity(signed))
        assert self.quantity_delta is not None
        if self.quantity_delta == ZERO:
            msg = "quantity_delta must be non-zero"
            raise ValueError(msg)
        if self.known_at < self.occurred_at:
            msg = "known_at must be >= occurred_at"
            raise ValueError(msg)
        if self.submitted_at < self.known_at:
            msg = "submitted_at must be >= known_at"
            raise ValueError(msg)
        return self

    @property
    def signed_quantity_delta(self) -> Decimal:
        assert self.quantity_delta is not None
        return self.quantity_delta


class RiskRuleResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: RiskRuleId
    status: RiskRuleStatus
    severity: RiskSeverity
    observed_value: str | None = Field(default=None, max_length=128)
    limit_value: str | None = Field(default=None, max_length=128)
    safe_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("safe_metadata")
    @classmethod
    def rule_metadata(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_safe_metadata(value)


class RiskAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    assessment_id: str = Field(min_length=64, max_length=64)
    assessment_hash: str = Field(min_length=64, max_length=64)
    policy_id: str = Field(min_length=1, max_length=128)
    policy_version: str = Field(min_length=1, max_length=32)
    policy_schema_version: str = Field(min_length=1, max_length=32)
    policy_fingerprint: str = Field(min_length=64, max_length=64)
    intent_id: str = Field(min_length=1, max_length=128)
    portfolio_id: PortfolioId
    portfolio_version: int = Field(ge=0)
    rule_results: tuple[RiskRuleResult, ...]
    final_action: RiskFinalAction
    evaluated_at: datetime
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)

    @field_validator("assessment_id", "assessment_hash", "policy_fingerprint")
    @classmethod
    def sha256_hex(cls, value: str) -> str:
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "hash fields must be sha256 hex"
            raise ValueError(msg)
        return text

    @field_validator("evaluated_at")
    @classmethod
    def utc_evaluated_at(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="evaluated_at")
