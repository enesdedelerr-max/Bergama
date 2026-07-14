"""Nested market-data orchestrator settings (Sprint 3 Issue #305)."""

from __future__ import annotations

from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class OrchestratorSettings(BaseModel):
    """Application-scoped pipeline configuration. No Kafka or provider settings.

    Disabled by default so production never constructs an active pipeline that
    can silently discard events through an implicit no-op sink.

    Capacity uses bounded in-flight admission control (not a durable queue).
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    dry_run: bool = False
    pipeline_name: str = Field(default="market-data-orchestrator", min_length=1, max_length=128)
    max_in_flight: int = Field(default=64, ge=1, le=10_000)
    admission_timeout_seconds: float = Field(default=0.05, gt=0, le=60.0)
    dedup_ttl_seconds: float = Field(default=3600.0, gt=0, le=86_400)
    dedup_max_entries: int = Field(default=50_000, ge=1, le=5_000_000)

    @field_validator("pipeline_name")
    @classmethod
    def strip_pipeline_name(cls, value: str) -> str:
        text = value.strip()
        if not text:
            msg = "pipeline_name must be non-empty"
            raise ValueError(msg)
        return text

    @model_validator(mode="after")
    def validate_dry_run_semantics(self) -> Self:
        if self.dry_run and not self.enabled:
            msg = "BERGAMA_ORCHESTRATOR__DRY_RUN requires BERGAMA_ORCHESTRATOR__ENABLED=true"
            raise ValueError(msg)
        return self

    def safe_summary(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "dry_run": self.dry_run,
            "pipeline_name": self.pipeline_name,
            "max_in_flight": self.max_in_flight,
            "admission_timeout_seconds": self.admission_timeout_seconds,
            "dedup_ttl_seconds": self.dedup_ttl_seconds,
            "dedup_max_entries": self.dedup_max_entries,
        }
