"""Historical Backfill Pipeline settings (#309).

Disabled by default. Default mode is dry_run. No provider or sink credentials —
reuse existing provider settings/secrets.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

BackfillDefaultMode = Literal["dry_run", "validate_only", "publish"]

_FORBIDDEN_CHECKPOINT_SEGMENTS = frozenset({".."})


class BackfillSettings(BaseModel):
    """Typed Backfill Pipeline configuration. Fail closed on invalid bounds/paths."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    enabled: bool = False
    default_mode: BackfillDefaultMode = "dry_run"
    max_time_range_days: int = Field(default=31, ge=1, le=366)
    max_records: int = Field(default=10_000, ge=1, le=100_000)
    max_slices: int = Field(default=366, ge=1, le=2_000)
    default_slice_days: int = Field(default=1, ge=1, le=31)
    max_concurrent_slices: int = Field(default=1, ge=1, le=8)
    max_in_flight_events: int = Field(default=1, ge=1, le=100)
    slice_retry_limit: int = Field(default=0, ge=0, le=5)
    slice_retry_initial_delay_seconds: float = Field(default=0.05, gt=0, le=60.0)
    slice_retry_max_delay_seconds: float = Field(default=1.0, gt=0, le=300.0)
    checkpoint_enabled: bool = True
    checkpoint_directory: str | None = None
    default_events_per_second: float | None = Field(default=None, gt=0, le=10_000.0)
    default_batch_size: int = Field(default=100, ge=1, le=10_000)

    @field_validator("checkpoint_directory", mode="before")
    @classmethod
    def blank_to_none(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            text = value.strip()
            return text or None
        return value

    @model_validator(mode="after")
    def validate_bounds_and_path(self) -> Self:
        if self.slice_retry_initial_delay_seconds > self.slice_retry_max_delay_seconds:
            msg = "slice_retry_initial_delay_seconds must be <= slice_retry_max_delay_seconds"
            raise ValueError(msg)
        if self.max_concurrent_slices > 1:
            # MVP: keep sequential by default settings; config may raise if >1 enabled.
            pass
        if self.enabled and self.checkpoint_enabled and not self.checkpoint_directory:
            msg = (
                "BERGAMA_BACKFILL__CHECKPOINT_DIRECTORY is required when "
                "backfill and checkpoints are enabled"
            )
            raise ValueError(msg)
        if self.checkpoint_directory is not None:
            self._validate_checkpoint_directory(self.checkpoint_directory)
        if self.default_mode == "publish" and self.enabled:
            msg = (
                "BERGAMA_BACKFILL__DEFAULT_MODE cannot be publish; "
                "side-effect modes require an explicit per-run PublishPort"
            )
            raise ValueError(msg)
        return self

    @staticmethod
    def _validate_checkpoint_directory(value: str) -> None:
        raw = value.strip()
        if not raw:
            msg = "checkpoint_directory must be non-empty"
            raise ValueError(msg)
        if "\x00" in raw:
            msg = "checkpoint_directory must not contain null bytes"
            raise ValueError(msg)
        path = Path(raw)
        if not path.is_absolute():
            msg = "checkpoint_directory must be an absolute path"
            raise ValueError(msg)
        for part in path.parts:
            if part in _FORBIDDEN_CHECKPOINT_SEGMENTS:
                msg = "checkpoint_directory must not contain path traversal segments"
                raise ValueError(msg)
        resolved_str = str(path)
        lowered = resolved_str.lower()
        forbidden_prefixes = ("/etc", "/proc", "/sys", "/dev", "/var/run")
        if any(lowered == p or lowered.startswith(f"{p}/") for p in forbidden_prefixes):
            msg = "checkpoint_directory points to a forbidden system path"
            raise ValueError(msg)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "default_mode": self.default_mode,
            "max_time_range_days": self.max_time_range_days,
            "max_records": self.max_records,
            "max_slices": self.max_slices,
            "default_slice_days": self.default_slice_days,
            "max_concurrent_slices": self.max_concurrent_slices,
            "max_in_flight_events": self.max_in_flight_events,
            "slice_retry_limit": self.slice_retry_limit,
            "checkpoint_enabled": self.checkpoint_enabled,
            "checkpoint_directory_configured": self.checkpoint_directory is not None,
            "default_events_per_second": self.default_events_per_second,
            "default_batch_size": self.default_batch_size,
        }
