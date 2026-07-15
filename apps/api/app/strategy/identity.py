"""Strategy identity and version contracts."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

_IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,127}$")
_VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$")


class StrategyIdentity(BaseModel):
    """Stable strategy identity for deterministic decisions and audit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    strategy_id: str = Field(min_length=1, max_length=128)
    strategy_version: str = Field(min_length=1, max_length=64)
    strategy_instance_id: str = Field(min_length=1, max_length=128)
    evaluation_version: str = Field(default="1.0.0", min_length=1, max_length=32)

    @field_validator("strategy_id", "strategy_instance_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        text = value.strip()
        if not _IDENTIFIER_RE.fullmatch(text):
            msg = "strategy identifiers must be lowercase stable tokens"
            raise ValueError(msg)
        return text

    @field_validator("strategy_version", "evaluation_version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        text = value.strip()
        if not _VERSION_RE.fullmatch(text):
            msg = "strategy versions must be stable non-empty tokens"
            raise ValueError(msg)
        return text
