"""Explicit immutable strategy state contracts."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from bergama_strategy_sdk.fingerprints import state_fingerprint
from bergama_strategy_sdk.versions import parse_semver


def _bounded_payload(value: dict[str, str]) -> dict[str, str]:
    if len(value) > 32:
        msg = "state payload may contain at most 32 entries"
        raise ValueError(msg)
    cleaned: dict[str, str] = {}
    for key, raw in sorted(value.items(), key=lambda item: str(item[0])):
        k = str(key).strip()
        v = str(raw).strip()
        if not k or len(k) > 64 or len(v) > 256:
            msg = "state payload keys/values exceed allowed bounds"
            raise ValueError(msg)
        cleaned[k] = v
    return cleaned


def _validate_state_schema_version(value: str) -> str:
    text = value.strip()
    parse_semver(text)
    return text


class PreviousStrategyState(BaseModel):
    """Immutable state input supplied by the host."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    state_schema_version: str = Field(min_length=1, max_length=32)
    state_id: str = Field(min_length=1, max_length=128)
    strategy_id: str | None = Field(default=None, max_length=128)
    strategy_instance_id: str | None = Field(default=None, max_length=128)
    payload: dict[str, str] = Field(default_factory=dict)

    @field_validator("state_schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        return _validate_state_schema_version(value)

    @field_validator("payload")
    @classmethod
    def bounded_payload(cls, value: dict[str, str]) -> dict[str, str]:
        return _bounded_payload(value)

    def fingerprint(self) -> str:
        return state_fingerprint(
            {
                "payload": self.payload,
                "state_id": self.state_id,
                "state_schema_version": self.state_schema_version,
                "strategy_id": self.strategy_id,
                "strategy_instance_id": self.strategy_instance_id,
            }
        )


class NextStrategyState(BaseModel):
    """Immutable state output returned by a strategy."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    state_schema_version: str = Field(min_length=1, max_length=32)
    state_id: str = Field(min_length=1, max_length=128)
    strategy_id: str | None = Field(default=None, max_length=128)
    strategy_instance_id: str | None = Field(default=None, max_length=128)
    payload: dict[str, str] = Field(default_factory=dict)

    @field_validator("state_schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        return _validate_state_schema_version(value)

    @field_validator("payload")
    @classmethod
    def bounded_payload(cls, value: dict[str, str]) -> dict[str, str]:
        return _bounded_payload(value)

    def fingerprint(self) -> str:
        return state_fingerprint(
            {
                "payload": self.payload,
                "state_id": self.state_id,
                "state_schema_version": self.state_schema_version,
                "strategy_id": self.strategy_id,
                "strategy_instance_id": self.strategy_instance_id,
            }
        )
