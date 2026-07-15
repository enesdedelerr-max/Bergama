"""Backfill checkpoint models (#309)."""

from __future__ import annotations

from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.market_data.backfill.models import (
    BackfillProvider,
    BackfillSlice,
    BackfillSourceKind,
    BackfillTerminalStatus,
)
from app.market_data.timing import require_utc_aware


class BackfillCheckpoint(BaseModel):
    """Dedicated durable checkpoint — not ReplayCheckpoint."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    backfill_id: str = Field(min_length=1, max_length=128)
    request_fingerprint: str = Field(min_length=64, max_length=64)
    provider: BackfillProvider
    source_kind: BackfillSourceKind
    current_slice: BackfillSlice | None = None
    completed_slices: tuple[str, ...] = ()
    provider_cursor: dict[str, str] = Field(default_factory=dict)
    last_successful_event_key: str | None = None
    processed_count: int = Field(default=0, ge=0)
    published_count: int = Field(default=0, ge=0)
    failed_count: int = Field(default=0, ge=0)
    started_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    completed: bool = False
    terminal_status: BackfillTerminalStatus | None = None

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
        return self

    def evolve(self, **changes: object) -> BackfillCheckpoint:
        data = self.model_dump(mode="python")
        data.update(changes)
        return BackfillCheckpoint.model_validate(data)
