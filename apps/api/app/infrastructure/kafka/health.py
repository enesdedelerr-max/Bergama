"""Kafka health check using client metadata (not TCP-only)."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.core.kafka_settings import KafkaSettings
from app.health.protocol import ERROR_CHECK_FAILED, ERROR_CHECK_UNAVAILABLE
from app.schemas.health import DependencyHealthResult, DependencyHealthStatus

MetadataFetcher = Callable[[], Awaitable[object]]


@dataclass(slots=True)
class KafkaHealthCheck:
    """Protocol-level Kafka check via cluster metadata."""

    settings: KafkaSettings
    timeout_seconds: float
    metadata_fetcher: MetadataFetcher | None = None
    name: str = "kafka"

    @property
    def required(self) -> bool:
        return bool(self.settings.health_required)

    async def check(self) -> DependencyHealthResult:
        started = time.perf_counter()
        if not self.settings.enabled:
            return DependencyHealthResult(
                name=self.name,
                status=DependencyHealthStatus.SKIPPED,
                required=self.required,
                latency_ms=_latency_ms(started),
                message="configuration missing",
            )
        if self.metadata_fetcher is None:
            return DependencyHealthResult(
                name=self.name,
                status=DependencyHealthStatus.FAIL,
                required=self.required,
                latency_ms=_latency_ms(started),
                message="dependency unavailable",
                error_code=ERROR_CHECK_UNAVAILABLE,
            )
        try:
            metadata = await self.metadata_fetcher()
            brokers = getattr(metadata, "brokers", None)
            if brokers is not None and len(brokers) == 0:
                return DependencyHealthResult(
                    name=self.name,
                    status=DependencyHealthStatus.FAIL,
                    required=self.required,
                    latency_ms=_latency_ms(started),
                    message="dependency unavailable",
                    error_code=ERROR_CHECK_UNAVAILABLE,
                )
            return DependencyHealthResult(
                name=self.name,
                status=DependencyHealthStatus.PASS,
                required=self.required,
                latency_ms=_latency_ms(started),
                message="kafka_metadata",
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
