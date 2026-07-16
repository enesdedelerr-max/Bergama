"""Order Management System identity constants and value models."""

from __future__ import annotations

import re
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, field_validator

ORDER_SCHEMA_VERSION: Final[str] = "oms-order-v1"
TRANSITION_ID_VERSION: Final[str] = "oms-transition:v1"
_CLIENT_ORDER_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:\-]{0,127}$")


class ClientOrderId(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    value: str = Field(min_length=1, max_length=128)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str) -> str:
        text = value.strip()
        if not _CLIENT_ORDER_ID_RE.fullmatch(text):
            msg = "client_order_id must be a stable token"
            raise ValueError(msg)
        return text


class OrderId(BaseModel):
    """Deterministic SHA-256 order identity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    value: str = Field(min_length=64, max_length=64)

    @field_validator("value")
    @classmethod
    def sha256_hex(cls, value: str) -> str:
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "order_id must be sha256 hex"
            raise ValueError(msg)
        return text
