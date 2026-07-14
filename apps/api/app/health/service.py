"""Application-owned health aggregation service."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from collections.abc import Sequence
from typing import Literal

from app.core.clock import Clock
from app.core.config import AppSettings
from app.core.log_context import generate_request_id, get_log_context
from app.core.logging import get_logger, structured_extra
from app.health.protocol import (
    ERROR_CHECK_FAILED,
    ERROR_CHECK_TIMEOUT,
    ERROR_INVALID_RESULT,
    HealthCheck,
)
from app.health.runtime_state import RuntimeLifecycleState, RuntimeState
from app.infrastructure.kafka.runtime import KafkaRuntime
from app.schemas.health import (
    DependencyHealthResult,
    DependencyHealthStatus,
    LivenessResponse,
    ReadinessResponse,
    StartupResponse,
)

logger = get_logger(__name__)

_LATENCY_DECIMALS = 3


class HealthService:
    """Run typed health checks with timeouts and deterministic aggregation.

    Application-scoped. Must not store request IDs or principals.
    """

    def __init__(
        self,
        *,
        settings: AppSettings,
        clock: Clock,
        runtime_state: RuntimeState,
        checks: Sequence[HealthCheck],
    ) -> None:
        self._settings = settings
        self._clock = clock
        self._runtime_state = runtime_state
        # Stable registration order — results sorted by this order, not completion.
        self._checks: tuple[HealthCheck, ...] = tuple(checks)

    @property
    def checks(self) -> tuple[HealthCheck, ...]:
        return self._checks

    def liveness(self) -> LivenessResponse:
        """Process-alive response — never invokes dependency checks."""
        return LivenessResponse(
            status="healthy",
            service=self._settings.service_name,
            version=self._settings.app_version,
            environment=self._settings.environment.value,
            timestamp=self._clock.now(),
            request_id=_resolve_request_id(),
        )

    def startup(self) -> tuple[StartupResponse, int]:
        """Return startup payload and HTTP status code."""
        probe = self._runtime_state.startup_probe_status()
        status_code = 200 if probe == "started" else 503
        body = StartupResponse(
            status=probe,  # type: ignore[arg-type]
            service=self._settings.service_name,
            version=self._settings.app_version,
            environment=self._settings.environment.value,
            timestamp=self._clock.now(),
            request_id=_resolve_request_id(),
        )
        return body, status_code

    async def readiness(self) -> tuple[ReadinessResponse, int]:
        """Run all checks concurrently and aggregate readiness."""
        logger.debug(
            "health readiness started",
            extra=structured_extra(
                event="health.readiness.started",
                source="health",
                check_count=len(self._checks),
            ),
        )
        results = await self._run_checks()
        aggregate = _aggregate_status(results)
        status_code = 503 if aggregate == "not_ready" else 200
        body = ReadinessResponse(
            status=aggregate,
            service=self._settings.service_name,
            version=self._settings.app_version,
            environment=self._settings.environment.value,
            timestamp=self._clock.now(),
            checks=results,
            request_id=_resolve_request_id(),
        )
        log_level = _readiness_log_level(aggregate)
        logger.log(
            log_level,
            "health readiness completed",
            extra=structured_extra(
                event="health.readiness.completed",
                source="health",
                aggregate_status=aggregate,
                status_code=status_code,
            ),
        )
        return body, status_code

    async def _run_checks(self) -> list[DependencyHealthResult]:
        if not self._checks:
            return []
        total = self._settings.health_total_timeout_seconds
        tasks = [
            asyncio.create_task(self._run_one(check), name=f"health:{check.name}")
            for check in self._checks
        ]
        done, pending = await asyncio.wait(tasks, timeout=total)
        results_by_name: dict[str, DependencyHealthResult] = {}
        for task in done:
            check_name = task.get_name().removeprefix("health:")
            try:
                results_by_name[check_name] = task.result()
            except Exception:
                results_by_name[check_name] = DependencyHealthResult(
                    name=check_name,
                    status=DependencyHealthStatus.FAIL,
                    required=next(c.required for c in self._checks if c.name == check_name),
                    latency_ms=0.0,
                    message="dependency unavailable",
                    error_code=ERROR_CHECK_FAILED,
                )
        for task in pending:
            check_name = task.get_name().removeprefix("health:")
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
            check = next(c for c in self._checks if c.name == check_name)
            results_by_name[check_name] = DependencyHealthResult(
                name=check.name,
                status=DependencyHealthStatus.TIMEOUT,
                required=check.required,
                latency_ms=round(total * 1000.0, _LATENCY_DECIMALS),
                message="timed out",
                error_code=ERROR_CHECK_TIMEOUT,
            )
        # Deterministic: registration order, never completion order.
        return [results_by_name[check.name] for check in self._checks]

    async def _run_one(self, check: HealthCheck) -> DependencyHealthResult:
        started = time.perf_counter()
        try:
            async with asyncio.timeout(check.timeout_seconds):
                result = await check.check()
        except TimeoutError:
            latency = _elapsed_ms(started)
            logger.warning(
                "health check timeout",
                extra=structured_extra(
                    event="health.check.timeout",
                    source="health",
                    check_name=check.name,
                    required=check.required,
                    status=DependencyHealthStatus.TIMEOUT.value,
                    latency_ms=latency,
                ),
            )
            return DependencyHealthResult(
                name=check.name,
                status=DependencyHealthStatus.TIMEOUT,
                required=check.required,
                latency_ms=latency,
                message="timed out",
                error_code=ERROR_CHECK_TIMEOUT,
            )
        except Exception:
            latency = _elapsed_ms(started)
            logger.error(
                "health check failed",
                exc_info=True,
                extra=structured_extra(
                    event="health.check.failed",
                    source="health",
                    check_name=check.name,
                    required=check.required,
                    status=DependencyHealthStatus.FAIL.value,
                    latency_ms=latency,
                ),
            )
            return DependencyHealthResult(
                name=check.name,
                status=DependencyHealthStatus.FAIL,
                required=check.required,
                latency_ms=latency,
                message="dependency unavailable",
                error_code=ERROR_CHECK_FAILED,
            )

        if result.name != check.name:
            return DependencyHealthResult(
                name=check.name,
                status=DependencyHealthStatus.FAIL,
                required=check.required,
                latency_ms=_elapsed_ms(started),
                message="invalid check result",
                error_code=ERROR_INVALID_RESULT,
            )
        if result.status is DependencyHealthStatus.FAIL:
            logger.warning(
                "health check failed",
                extra=structured_extra(
                    event="health.check.failed",
                    source="health",
                    check_name=result.name,
                    required=result.required,
                    status=result.status.value,
                    latency_ms=result.latency_ms,
                ),
            )
        return result


def build_default_health_checks(
    settings: AppSettings,
    *,
    kafka_runtime: KafkaRuntime | None = None,
    registry_service: object | None = None,
) -> tuple[HealthCheck, ...]:
    """Register Sprint 2 dependency checks."""
    from app.health.checks import TcpConnectivityCheck
    from app.infrastructure.kafka.health import KafkaHealthCheck
    from app.registry.health import RegistryHealthCheck
    from app.registry.service import RegistryService

    timeout = settings.health_check_timeout_seconds
    postgres_required = bool(settings.postgres_required)
    redis_required = bool(settings.redis_required)

    async def _kafka_metadata() -> object:
        if kafka_runtime is None or not kafka_runtime.started:
            msg = "kafka client is not started"
            raise RuntimeError(msg)
        return await kafka_runtime.fetch_metadata()

    kafka_check = KafkaHealthCheck(
        settings=settings.kafka,
        timeout_seconds=timeout,
        metadata_fetcher=_kafka_metadata if settings.kafka.enabled else None,
    )
    if isinstance(registry_service, RegistryService):
        registry_check: HealthCheck = RegistryHealthCheck(
            service=registry_service,
            timeout_seconds=timeout,
        )
    else:
        # Disabled / absent: explicit skipped check via ephemeral service.
        registry_check = RegistryHealthCheck(
            service=RegistryService(settings.registry),
            timeout_seconds=timeout,
        )
    return (
        TcpConnectivityCheck(
            name="postgres_tcp",
            required=postgres_required,
            timeout_seconds=timeout,
            host=settings.postgres_host,
            port=settings.postgres_port,
        ),
        TcpConnectivityCheck(
            name="redis_tcp",
            required=redis_required,
            timeout_seconds=timeout,
            host=settings.redis_host,
            port=settings.redis_port,
        ),
        kafka_check,
        registry_check,
    )


def _aggregate_status(
    results: Sequence[DependencyHealthResult],
) -> Literal["ready", "degraded", "not_ready"]:
    blocking = {
        DependencyHealthStatus.FAIL,
        DependencyHealthStatus.TIMEOUT,
        DependencyHealthStatus.SKIPPED,
    }
    required_failed = any(r.required and r.status in blocking for r in results)
    if required_failed:
        return "not_ready"
    optional_failed = any(
        (not r.required)
        and r.status in {DependencyHealthStatus.FAIL, DependencyHealthStatus.TIMEOUT}
        for r in results
    )
    if optional_failed:
        return "degraded"
    return "ready"


def _readiness_log_level(aggregate: str) -> int:
    if aggregate == "ready":
        return logging.DEBUG
    if aggregate == "degraded":
        return logging.WARNING
    return logging.ERROR


def _resolve_request_id() -> str:
    ctx = get_log_context()
    if ctx.request_id:
        return ctx.request_id
    return generate_request_id()


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, _LATENCY_DECIMALS)


def log_startup_state_change(
    runtime_state: RuntimeState,
    *,
    previous: RuntimeLifecycleState | None,
) -> None:
    """Emit a structured lifecycle transition log."""
    logger.info(
        "health startup state changed",
        extra=structured_extra(
            event="health.startup.state_changed",
            source="health",
            previous=previous.value if previous is not None else None,
            status=runtime_state.state.value,
        ),
    )
