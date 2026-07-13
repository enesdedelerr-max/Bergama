"""Explicit application-scoped dependency container (Issues #206–#208A)."""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import AsyncExitStack
from dataclasses import dataclass, field

from app.core.clock import Clock, JtiGenerator, SystemClock, UuidJtiGenerator
from app.core.config import AppSettings
from app.core.logging import get_logger, structured_extra
from app.events.ports import EventHandler
from app.events.retry import RetryPolicy
from app.events.topics import TopicRegistry
from app.health.protocol import HealthCheck
from app.health.runtime_state import RuntimeState
from app.health.service import HealthService, build_default_health_checks
from app.infrastructure.kafka.runtime import KafkaRuntime, build_kafka_runtime
from app.services.token_service import TokenService

logger = get_logger(__name__)


@dataclass(slots=True)
class AppContainer:
    """Long-lived runtime dependencies for one FastAPI application instance."""

    settings: AppSettings
    clock: Clock
    jti_generator: JtiGenerator
    token_service: TokenService
    runtime_state: RuntimeState
    health_service: HealthService
    topic_registry: TopicRegistry
    kafka_runtime: KafkaRuntime | None
    _exit_stack: AsyncExitStack = field(default_factory=AsyncExitStack, repr=False, compare=False)
    _closed: bool = field(default=False, init=False, repr=False, compare=False)

    async def aclose(self) -> None:
        """Release owned async resources. Idempotent."""
        if self._closed:
            return
        self._closed = True
        try:
            if self.kafka_runtime is not None:
                await self.kafka_runtime.stop()
            await self._exit_stack.aclose()
        except Exception:
            logger.error(
                "container cleanup failed",
                exc_info=True,
                extra=structured_extra(
                    event="container.cleanup.failed",
                    source="container",
                ),
            )
            raise


def build_container(
    settings: AppSettings,
    *,
    clock: Clock | None = None,
    jti_generator: JtiGenerator | None = None,
    token_service: TokenService | None = None,
    runtime_state: RuntimeState | None = None,
    health_checks: Sequence[HealthCheck] | None = None,
    health_service: HealthService | None = None,
    kafka_runtime: KafkaRuntime | None = None,
    event_handler: EventHandler | None = None,
    retry_policy: RetryPolicy | None = None,
) -> AppContainer:
    """Construct an application container. All long-lived deps are owned here."""
    resolved_clock = clock if clock is not None else SystemClock()
    resolved_jti = jti_generator if jti_generator is not None else UuidJtiGenerator()
    resolved_token = (
        token_service
        if token_service is not None
        else TokenService(
            settings,
            clock=resolved_clock,
            jti_factory=resolved_jti,
        )
    )
    resolved_runtime = runtime_state if runtime_state is not None else RuntimeState()
    topic_registry = TopicRegistry(topic_prefix=settings.kafka.topic_prefix)
    resolved_kafka: KafkaRuntime | None
    if kafka_runtime is not None:
        resolved_kafka = kafka_runtime
    elif settings.kafka.enabled:
        resolved_kafka = build_kafka_runtime(
            settings.kafka,
            handler=event_handler,
            retry_policy=retry_policy,
        )
    else:
        resolved_kafka = None

    resolved_checks = (
        tuple(health_checks)
        if health_checks is not None
        else build_default_health_checks(settings, kafka_runtime=resolved_kafka)
    )
    resolved_health = (
        health_service
        if health_service is not None
        else HealthService(
            settings=settings,
            clock=resolved_clock,
            runtime_state=resolved_runtime,
            checks=resolved_checks,
        )
    )
    return AppContainer(
        settings=settings,
        clock=resolved_clock,
        jti_generator=resolved_jti,
        token_service=resolved_token,
        runtime_state=resolved_runtime,
        health_service=resolved_health,
        topic_registry=topic_registry,
        kafka_runtime=resolved_kafka,
    )
