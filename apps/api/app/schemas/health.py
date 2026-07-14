"""Versioned health API contracts (Issue #207)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthStatus(StrEnum):
    """Coarse process health for liveness."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class DependencyHealthStatus(StrEnum):
    """Per-dependency check outcome."""

    PASS = "pass"
    FAIL = "fail"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


class DependencyHealthResult(BaseModel):
    """Single dependency check result — no secrets or connection strings."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    status: DependencyHealthStatus
    required: bool
    latency_ms: float = Field(ge=0)
    message: str | None = None
    error_code: str | None = None


class LivenessResponse(BaseModel):
    """Process liveness — no dependency checks."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["healthy"] = "healthy"
    service: str
    version: str
    environment: str
    timestamp: datetime
    request_id: str


class ReadinessResponse(BaseModel):
    """Traffic readiness with structured dependency results."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ready", "degraded", "not_ready"]
    service: str
    version: str
    environment: str
    timestamp: datetime
    checks: list[DependencyHealthResult]
    request_id: str


class StartupResponse(BaseModel):
    """Application lifecycle startup probe."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["starting", "started", "failed"]
    service: str
    version: str
    environment: str
    timestamp: datetime
    request_id: str
