"""Data quality and late-arrival / revision flags."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DataQualityFlags(BaseModel):
    """Explicit quality / PIT handling flags — no silent defaults for revisions."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    is_late: bool = False
    is_revision: bool = False
    is_stale: bool = False
    is_estimated: bool = False
    is_incomplete: bool = False
    revision_of_event_id: str | None = Field(default=None, max_length=128)
    late_arrival_lag_ms: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_revision_pair(self) -> Self:
        if self.is_revision and not self.revision_of_event_id:
            msg = "is_revision requires revision_of_event_id"
            raise ValueError(msg)
        if self.revision_of_event_id and not self.is_revision:
            msg = "revision_of_event_id requires is_revision=true"
            raise ValueError(msg)
        if self.is_late and self.late_arrival_lag_ms is None:
            # Lag may be unknown; allow None. Consumer may still mark is_late.
            return self
        return self
