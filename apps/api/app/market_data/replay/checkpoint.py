"""Replay checkpoint models (#308)."""

from __future__ import annotations

from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.market_data.replay.models import (
    ReplayCursor,
    ReplayMode,
    ReplaySourceType,
    ReplayTerminalStatus,
)
from app.market_data.timing import require_utc_aware


class ReplayCheckpoint(BaseModel):
    """Minimum durable checkpoint for resume-after-success."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    replay_id: str = Field(min_length=1, max_length=128)
    request_fingerprint: str = Field(min_length=64, max_length=64)
    mode: ReplayMode
    source: ReplaySourceType = "iceberg"
    last_cursor: ReplayCursor | None = None
    processed_count: int = Field(default=0, ge=0)
    succeeded_count: int = Field(default=0, ge=0)
    failed_count: int = Field(default=0, ge=0)
    started_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    completed: bool = False
    terminal_status: ReplayTerminalStatus | None = None

    @field_validator("replay_id", "request_fingerprint")
    @classmethod
    def strip_ids(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "checkpoint id field must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator("request_fingerprint")
    @classmethod
    def hex_fingerprint(cls, value: str) -> str:
        text = value.strip().lower()
        if len(text) != 64 or any(c not in "0123456789abcdef" for c in text):
            msg = "request_fingerprint must be sha256 hex"
            raise ValueError(msg)
        return text

    @field_validator("started_at", "updated_at", "completed_at")
    @classmethod
    def utc_times(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return require_utc_aware(value, field_name="checkpoint_time")

    @model_validator(mode="after")
    def validate_completion(self) -> Self:
        if self.completed and self.completed_at is None:
            msg = "completed checkpoint requires completed_at"
            raise ValueError(msg)
        if self.completed and self.terminal_status is None:
            msg = "completed checkpoint requires terminal_status"
            raise ValueError(msg)
        if self.failed_count < 0 or self.succeeded_count < 0 or self.processed_count < 0:
            msg = "counts must be non-negative"
            raise ValueError(msg)
        return self

    def evolve(self, **changes: object) -> ReplayCheckpoint:
        data = self.model_dump(mode="python")
        data.update(changes)
        return ReplayCheckpoint.model_validate(data)
