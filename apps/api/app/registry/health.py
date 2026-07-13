"""Registry readiness health check."""

from __future__ import annotations

import time
from dataclasses import dataclass

from app.health.protocol import ERROR_CHECK_FAILED, ERROR_CHECK_UNAVAILABLE
from app.registry.service import RegistryService
from app.schemas.health import DependencyHealthResult, DependencyHealthStatus


@dataclass(slots=True)
class RegistryHealthCheck:
    """Reports whether the registry catalog is loaded (no paths/payloads)."""

    service: RegistryService
    timeout_seconds: float
    name: str = "registry"

    @property
    def required(self) -> bool:
        settings = self.service.settings
        return bool(settings.health_required or settings.required_registry_ids)

    async def check(self) -> DependencyHealthResult:
        started = time.perf_counter()
        settings = self.service.settings
        if not settings.enabled:
            return DependencyHealthResult(
                name=self.name,
                status=DependencyHealthStatus.SKIPPED,
                required=self.required,
                latency_ms=_latency_ms(started),
                message="configuration missing",
            )
        if not self.service.is_loaded:
            return DependencyHealthResult(
                name=self.name,
                status=DependencyHealthStatus.FAIL,
                required=self.required,
                latency_ms=_latency_ms(started),
                message="dependency unavailable",
                error_code=ERROR_CHECK_UNAVAILABLE,
            )
        try:
            summary = self.service.safe_summary()
            return DependencyHealthResult(
                name=self.name,
                status=DependencyHealthStatus.PASS,
                required=self.required,
                latency_ms=_latency_ms(started),
                message=f"registry_count={summary.count}",
            )
        except Exception:
            return DependencyHealthResult(
                name=self.name,
                status=DependencyHealthStatus.FAIL,
                required=self.required,
                latency_ms=_latency_ms(started),
                message="dependency unavailable",
                error_code=ERROR_CHECK_FAILED,
            )


def _latency_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 3)
