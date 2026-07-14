"""Replay engine settings (#308).

Disabled by default. Default mode is dry_run. No production sink configuration
and no duplicated Iceberg credentials — catalog settings are reused from
IcebergWriterSettings.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ReplayDefaultMode = Literal["dry_run", "validate_only", "republish", "custom_sink"]

_FORBIDDEN_CHECKPOINT_SEGMENTS = frozenset({".."})


class ReplaySettings(BaseModel):
    """Typed Replay Engine configuration. Fail closed on invalid bounds/paths."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    enabled: bool = False
    default_mode: ReplayDefaultMode = "dry_run"
    max_time_range_days: int = Field(default=31, ge=1, le=366)
    max_records: int = Field(default=10_000, ge=1, le=100_000)
    default_batch_size: int = Field(default=100, ge=1, le=10_000)
    max_batch_size: int = Field(default=1_000, ge=1, le=10_000)
    default_max_in_flight: int = Field(default=1, ge=1, le=100)
    checkpoint_enabled: bool = True
    checkpoint_directory: str | None = None
    default_events_per_second: float | None = Field(default=None, gt=0, le=10_000.0)

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
        if self.default_batch_size > self.max_batch_size:
            msg = "default_batch_size must be <= max_batch_size"
            raise ValueError(msg)
        if self.default_max_in_flight > self.max_batch_size:
            msg = "default_max_in_flight must be <= max_batch_size"
            raise ValueError(msg)
        if self.enabled and self.checkpoint_enabled and not self.checkpoint_directory:
            msg = (
                "BERGAMA_REPLAY__CHECKPOINT_DIRECTORY is required when "
                "replay and checkpoints are enabled"
            )
            raise ValueError(msg)
        if self.checkpoint_directory is not None:
            self._validate_checkpoint_directory(self.checkpoint_directory)
        if self.default_mode not in {"dry_run", "validate_only", "republish", "custom_sink"}:
            msg = "default_mode is not supported"
            raise ValueError(msg)
        if self.default_mode in {"republish", "custom_sink"} and self.enabled:
            # Safe defaults: never auto-select a production sink via settings alone.
            msg = (
                "BERGAMA_REPLAY__DEFAULT_MODE cannot be republish or custom_sink; "
                "side-effect modes require an explicit per-run sink"
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
        # Reject obviously unsafe roots (never write under system dirs).
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
            "default_batch_size": self.default_batch_size,
            "max_batch_size": self.max_batch_size,
            "default_max_in_flight": self.default_max_in_flight,
            "checkpoint_enabled": self.checkpoint_enabled,
            "checkpoint_directory_configured": self.checkpoint_directory is not None,
            "default_events_per_second": self.default_events_per_second,
        }
