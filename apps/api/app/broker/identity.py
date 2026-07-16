"""Broker identity value models (#405)."""

from __future__ import annotations

import re
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, field_validator

BROKER_SCHEMA_VERSION: Final[str] = "broker-v1"
SUBMISSION_ID_VERSION: Final[str] = "broker-submission:v1"
BROKER_EVENT_ID_VERSION: Final[str] = "broker-event:v1"
_TOKEN_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:\-]{0,127}$")


class BrokerName(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    value: str = Field(min_length=1, max_length=64)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str) -> str:
        text = value.strip()
        if not _TOKEN_RE.fullmatch(text):
            msg = "broker_name must be a stable token"
            raise ValueError(msg)
        return text


class BrokerAccountId(BaseModel):
    """Broker-side account reference. Never a provider account object."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    value: str = Field(min_length=1, max_length=128)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str) -> str:
        text = value.strip()
        if not _TOKEN_RE.fullmatch(text):
            msg = "broker_account_id must be a stable token"
            raise ValueError(msg)
        return text


class BrokerIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    broker_name: BrokerName
    broker_account_id: BrokerAccountId
