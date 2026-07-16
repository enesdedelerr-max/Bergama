"""Portfolio identity value models."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

_IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9._:\-]{0,127}$")


class AccountId(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    value: str = Field(min_length=1, max_length=128)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str) -> str:
        text = value.strip()
        if not _IDENTIFIER_RE.fullmatch(text):
            msg = "account_id must be a lowercase stable token"
            raise ValueError(msg)
        return text


class PortfolioId(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    value: str = Field(min_length=1, max_length=128)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str) -> str:
        text = value.strip()
        if not _IDENTIFIER_RE.fullmatch(text):
            msg = "portfolio_id must be a lowercase stable token"
            raise ValueError(msg)
        return text
