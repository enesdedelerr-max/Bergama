"""Nested market-data orchestrator settings (Sprint 3 Issues #305 / #306)."""

from __future__ import annotations

from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class OrchestratorSettings(BaseModel):
    """Application-scoped pipeline configuration.

    Provider and Kafka bootstrap settings are never owned here. Publish sink
    selection is explicit via ``publish_backend`` so enabling Kafka alone never
    silently wires a Kafka publish adapter.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    dry_run: bool = False
    # none = inject PublishPort or dry_run; kafka = build KafkaPublishAdapter.
    publish_backend: Literal["none", "kafka"] = "none"
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
    def validate_publish_semantics(self) -> Self:
        if self.dry_run and not self.enabled:
            msg = "BERGAMA_ORCHESTRATOR__DRY_RUN requires BERGAMA_ORCHESTRATOR__ENABLED=true"
            raise ValueError(msg)
        if self.publish_backend == "kafka" and not self.enabled:
            msg = (
                "BERGAMA_ORCHESTRATOR__PUBLISH_BACKEND=kafka requires "
                "BERGAMA_ORCHESTRATOR__ENABLED=true"
            )
            raise ValueError(msg)
        if self.dry_run and self.publish_backend == "kafka":
            msg = (
                "BERGAMA_ORCHESTRATOR__DRY_RUN cannot be combined with "
                "BERGAMA_ORCHESTRATOR__PUBLISH_BACKEND=kafka"
            )
            raise ValueError(msg)
        return self

    def safe_summary(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "dry_run": self.dry_run,
            "publish_backend": self.publish_backend,
            "pipeline_name": self.pipeline_name,
            "max_in_flight": self.max_in_flight,
            "admission_timeout_seconds": self.admission_timeout_seconds,
            "dedup_ttl_seconds": self.dedup_ttl_seconds,
            "dedup_max_entries": self.dedup_max_entries,
        }
