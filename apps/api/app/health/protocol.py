"""Health check protocol and error codes."""

from __future__ import annotations

from typing import Protocol

from app.schemas.health import DependencyHealthResult

ERROR_CHECK_FAILED = "health.check_failed"
ERROR_CHECK_TIMEOUT = "health.check_timeout"
ERROR_CHECK_UNAVAILABLE = "health.check_unavailable"
ERROR_INVALID_RESULT = "health.invalid_result"
ERROR_STARTUP_FAILED = "health.startup_failed"


class HealthCheck(Protocol):
    """Typed dependency health check."""

    @property
    def name(self) -> str:
        """Stable check name."""
        ...

    @property
    def required(self) -> bool:
        """Whether failure blocks readiness."""
        ...

    @property
    def timeout_seconds(self) -> float:
        """Per-check timeout budget."""
        ...

    async def check(self) -> DependencyHealthResult:
        """Execute the check and return a typed result."""
        ...
