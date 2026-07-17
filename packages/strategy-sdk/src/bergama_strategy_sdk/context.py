"""Immutable deterministic execution context — no wall clock."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrategyExecutionContext(BaseModel):
    """Injected deterministic context for one strategy evaluation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    execution_id: str = Field(min_length=1, max_length=128)
    strategy_id: str = Field(min_length=1, max_length=128)
    strategy_version: str = Field(min_length=1, max_length=64)
    strategy_instance_id: str = Field(min_length=1, max_length=128)
    run_id: str = Field(min_length=1, max_length=128)
    session_id: str = Field(min_length=1, max_length=128)
    evaluation_time: datetime
    sdk_schema_version: str = Field(min_length=1, max_length=32)
    runtime_protocol_version: str = Field(min_length=1, max_length=32)
    feature_schema_version: str = Field(min_length=1, max_length=32)
    config_schema_version: str = Field(min_length=1, max_length=32)
    strategy_fingerprint: str = Field(min_length=64, max_length=64)
    feature_fingerprint: str = Field(min_length=64, max_length=64)
    configuration_fingerprint: str = Field(min_length=64, max_length=64)
    execution_fingerprint: str = Field(min_length=64, max_length=64)
    correlation_id: str | None = Field(default=None, max_length=128)
    causation_id: str | None = Field(default=None, max_length=128)
    replay_id: str | None = Field(default=None, max_length=128)

    @field_validator(
        "strategy_fingerprint",
        "feature_fingerprint",
        "configuration_fingerprint",
        "execution_fingerprint",
    )
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "fingerprint fields must be sha256 hex"
            raise ValueError(msg)
        return text

    @field_validator("evaluation_time")
    @classmethod
    def utc_evaluation_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            msg = "evaluation_time must be timezone-aware UTC"
            raise ValueError(msg)
        if value.utcoffset() != timedelta(0):
            msg = "evaluation_time must use an exact UTC offset"
            raise ValueError(msg)
        return value.astimezone(UTC)
