"""Data-quality subsystem settings (#310)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class DataQualitySettings(BaseModel):
    """Safe, non-disruptive defaults for canonical data-quality evaluation."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    required: bool = False
    observe_only: bool = True
    reject_on_error: bool = False
    halt_on_critical: bool = False
    quarantine_enabled: bool = False
    aggregation_window_seconds: int = Field(default=300, ge=1, le=86_400)
    max_tracked_instruments: int = Field(default=128, ge=0, le=10_000)
    max_problem_dimensions: int = Field(default=20, ge=1, le=1_000)
    snapshot_interval_seconds: int = Field(default=60, ge=1, le=86_400)
    policy_file: str | None = Field(default=None, max_length=4096)
    policy_required: bool = False
    policy_max_file_bytes: int = Field(default=262_144, ge=1, le=5_242_880)
    readiness_fail_on_critical_halt: bool = False

    @field_validator("policy_file")
    @classmethod
    def validate_policy_file(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if not text:
            return None
        lowered = text.lower().replace("\\", "/")
        if "://" in lowered:
            msg = "data-quality policy_file must be a local filesystem path"
            raise ValueError(msg)
        if "\x00" in text:
            msg = "data-quality policy_file contains an invalid path character"
            raise ValueError(msg)
        forbidden_markers = (".secrets", "secrets.env", "/secrets/")
        if any(marker in lowered for marker in forbidden_markers):
            msg = "data-quality policy_file must not reference secret files"
            raise ValueError(msg)
        suffix = Path(text).suffix.lower()
        if suffix and suffix not in {".yaml", ".yml", ".json"}:
            msg = "data-quality policy_file must be .yaml, .yml or .json"
            raise ValueError(msg)
        return text

    @model_validator(mode="after")
    def validate_semantics(self) -> Self:
        if self.required and not self.enabled:
            msg = "BERGAMA_DATA_QUALITY__REQUIRED requires DATA_QUALITY__ENABLED=true"
            raise ValueError(msg)
        if self.policy_required and self.policy_file is None:
            msg = "BERGAMA_DATA_QUALITY__POLICY_FILE is required when policy_required=true"
            raise ValueError(msg)
        if self.quarantine_enabled and self.observe_only:
            # Observe-only may still build quarantine policy, but it must not act on it.
            return self
        return self

    def safe_summary(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "required": self.required,
            "observe_only": self.observe_only,
            "reject_on_error": self.reject_on_error,
            "halt_on_critical": self.halt_on_critical,
            "quarantine_enabled": self.quarantine_enabled,
            "aggregation_window_seconds": self.aggregation_window_seconds,
            "max_tracked_instruments": self.max_tracked_instruments,
            "max_problem_dimensions": self.max_problem_dimensions,
            "snapshot_interval_seconds": self.snapshot_interval_seconds,
            "policy_file_configured": self.policy_file is not None,
            "policy_required": self.policy_required,
            "policy_max_file_bytes": self.policy_max_file_bytes,
            "readiness_fail_on_critical_halt": self.readiness_fail_on_critical_halt,
        }
