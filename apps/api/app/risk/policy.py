"""Immutable RiskPolicy and deterministic fingerprint."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.portfolio.decimal import (
    ZERO,
    canonical_decimal,
    parse_portfolio_decimal,
    quantize_money,
    require_positive,
)
from app.portfolio.models import normalize_currency
from app.risk.errors import RiskDecimalError
from app.risk.hashing import compute_policy_fingerprint
from app.risk.identity import POLICY_SCHEMA_VERSION


class RiskPolicy(BaseModel):
    """Strict immutable risk limits. Evaluation input only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    risk_policy_id: str = Field(min_length=1, max_length=128)
    risk_policy_version: str = Field(min_length=1, max_length=32)
    policy_schema_version: str = Field(default=POLICY_SCHEMA_VERSION, min_length=1, max_length=32)
    policy_fingerprint: str | None = Field(default=None, min_length=64, max_length=64)

    base_currency: str = Field(default="USD", min_length=3, max_length=3)
    kill_switch_enabled: bool = False
    allow_short_positions: bool = False

    max_order_notional: Decimal
    max_position_notional: Decimal
    max_gross_exposure: Decimal
    max_net_exposure: Decimal
    max_concentration_ratio: Decimal

    max_snapshot_age_seconds: int = Field(ge=0, le=86_400)
    max_mark_age_seconds: int = Field(ge=0, le=86_400)

    allowed_instruments: tuple[str, ...] | None = None

    @field_validator("risk_policy_id", "risk_policy_version", "policy_schema_version")
    @classmethod
    def clean_tokens(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "policy identity fields must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator("base_currency")
    @classmethod
    def normalize_base_currency(cls, value: str) -> str:
        return normalize_currency(value)

    @field_validator(
        "max_order_notional",
        "max_position_notional",
        "max_gross_exposure",
        "max_net_exposure",
        mode="before",
    )
    @classmethod
    def parse_money_limits(cls, value: object) -> Decimal:
        try:
            return require_positive(
                quantize_money(parse_portfolio_decimal(value, field_name="money_limit")),
                field_name="money_limit",
            )
        except Exception as exc:
            raise RiskDecimalError(detail="money_limit") from exc

    @field_validator("max_concentration_ratio", mode="before")
    @classmethod
    def parse_concentration(cls, value: object) -> Decimal:
        try:
            parsed = parse_portfolio_decimal(value, field_name="max_concentration_ratio")
        except Exception as exc:
            raise RiskDecimalError(detail="max_concentration_ratio") from exc
        if parsed <= ZERO or parsed > Decimal("1"):
            msg = "max_concentration_ratio must be in (0, 1]"
            raise ValueError(msg)
        return parsed

    @field_validator("policy_fingerprint")
    @classmethod
    def sha256_or_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "policy_fingerprint must be sha256 hex"
            raise ValueError(msg)
        return text

    @field_validator("allowed_instruments")
    @classmethod
    def normalize_allowed(cls, value: tuple[str, ...] | None) -> tuple[str, ...] | None:
        if value is None:
            return None
        cleaned = tuple(sorted({item.strip() for item in value if item.strip()}))
        return cleaned

    @model_validator(mode="after")
    def attach_fingerprint(self) -> Self:
        expected = compute_policy_fingerprint(self)
        if self.policy_fingerprint is None:
            object.__setattr__(self, "policy_fingerprint", expected)
        elif self.policy_fingerprint != expected:
            msg = "policy_fingerprint does not match business fields"
            raise ValueError(msg)
        return self

    def fingerprint(self) -> str:
        assert self.policy_fingerprint is not None
        return self.policy_fingerprint

    def fingerprint_payload(self) -> dict[str, Any]:
        allowed = list(self.allowed_instruments) if self.allowed_instruments else None
        return {
            "allow_short_positions": self.allow_short_positions,
            "allowed_instruments": allowed,
            "base_currency": self.base_currency,
            "kill_switch_enabled": self.kill_switch_enabled,
            "max_concentration_ratio": canonical_decimal(self.max_concentration_ratio),
            "max_gross_exposure": canonical_decimal(self.max_gross_exposure),
            "max_mark_age_seconds": self.max_mark_age_seconds,
            "max_net_exposure": canonical_decimal(self.max_net_exposure),
            "max_order_notional": canonical_decimal(self.max_order_notional),
            "max_position_notional": canonical_decimal(self.max_position_notional),
            "max_snapshot_age_seconds": self.max_snapshot_age_seconds,
            "policy_schema_version": self.policy_schema_version,
            "risk_policy_version": self.risk_policy_version,
        }
