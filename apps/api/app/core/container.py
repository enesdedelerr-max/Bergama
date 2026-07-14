"""Explicit application-scoped dependency container (Issues #206–#209 / #302–#304A)."""

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
from app.infrastructure.finnhub.fundamentals import FinnhubFundamentalsConnector
from app.infrastructure.finnhub.http import FinnhubHttpClient
from app.infrastructure.finnhub.reference import FinnhubReferenceConnector
from app.infrastructure.kafka.runtime import KafkaRuntime, build_kafka_runtime
from app.infrastructure.polygon.historical import PolygonHistoricalConnector
from app.infrastructure.polygon.http import PolygonHttpClient
from app.infrastructure.polygon.realtime import PolygonRealtimeConnector
from app.registry.service import RegistryService
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
    registry_service: RegistryService
    polygon_http: PolygonHttpClient | None
    polygon_historical: PolygonHistoricalConnector | None
    polygon_realtime: PolygonRealtimeConnector | None
    finnhub_http: FinnhubHttpClient | None
    finnhub_reference: FinnhubReferenceConnector | None
    finnhub_fundamentals: FinnhubFundamentalsConnector | None
    _exit_stack: AsyncExitStack = field(default_factory=AsyncExitStack, repr=False, compare=False)
    _closed: bool = field(default=False, init=False, repr=False, compare=False)

    async def aclose(self) -> None:
        """Release owned async resources. Idempotent."""
        if self._closed:
            return
        self._closed = True
        try:
            await self.registry_service.close()
            if self.kafka_runtime is not None:
                await self.kafka_runtime.stop()
            if self.polygon_realtime is not None:
                await self.polygon_realtime.aclose()
            if self.polygon_http is not None:
                await self.polygon_http.aclose()
            if self.finnhub_http is not None:
                await self.finnhub_http.aclose()
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
    registry_service: RegistryService | None = None,
    polygon_http: PolygonHttpClient | None = None,
    polygon_historical: PolygonHistoricalConnector | None = None,
    polygon_realtime: PolygonRealtimeConnector | None = None,
    finnhub_http: FinnhubHttpClient | None = None,
    finnhub_reference: FinnhubReferenceConnector | None = None,
    finnhub_fundamentals: FinnhubFundamentalsConnector | None = None,
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

    resolved_registry = (
        registry_service
        if registry_service is not None
        else RegistryService(settings.registry, clock=resolved_clock)
    )

    resolved_polygon_http: PolygonHttpClient | None
    resolved_polygon_historical: PolygonHistoricalConnector | None
    resolved_polygon_realtime: PolygonRealtimeConnector | None
    if polygon_http is not None:
        resolved_polygon_http = polygon_http
        resolved_polygon_historical = (
            polygon_historical
            if polygon_historical is not None
            else PolygonHistoricalConnector(polygon_http, clock=resolved_clock)
        )
    elif settings.polygon.enabled:
        resolved_polygon_http = PolygonHttpClient(settings.polygon)
        resolved_polygon_historical = PolygonHistoricalConnector(
            resolved_polygon_http,
            clock=resolved_clock,
        )
    else:
        resolved_polygon_http = None
        resolved_polygon_historical = None

    if polygon_realtime is not None:
        resolved_polygon_realtime = polygon_realtime
    elif settings.polygon.enabled and settings.polygon.websocket_enabled:
        resolved_polygon_realtime = PolygonRealtimeConnector(
            settings.polygon,
            clock=resolved_clock,
        )
    else:
        resolved_polygon_realtime = None

    resolved_finnhub_http: FinnhubHttpClient | None
    resolved_finnhub_reference: FinnhubReferenceConnector | None
    resolved_finnhub_fundamentals: FinnhubFundamentalsConnector | None
    if finnhub_http is not None:
        resolved_finnhub_http = finnhub_http
        resolved_finnhub_reference = (
            finnhub_reference
            if finnhub_reference is not None
            else FinnhubReferenceConnector(finnhub_http, clock=resolved_clock)
        )
        resolved_finnhub_fundamentals = (
            finnhub_fundamentals
            if finnhub_fundamentals is not None
            else FinnhubFundamentalsConnector(finnhub_http, clock=resolved_clock)
        )
    elif settings.finnhub.enabled:
        resolved_finnhub_http = FinnhubHttpClient(settings.finnhub)
        resolved_finnhub_reference = FinnhubReferenceConnector(
            resolved_finnhub_http,
            clock=resolved_clock,
        )
        resolved_finnhub_fundamentals = FinnhubFundamentalsConnector(
            resolved_finnhub_http,
            clock=resolved_clock,
        )
    else:
        resolved_finnhub_http = None
        resolved_finnhub_reference = None
        resolved_finnhub_fundamentals = None

    resolved_checks = (
        tuple(health_checks)
        if health_checks is not None
        else build_default_health_checks(
            settings,
            kafka_runtime=resolved_kafka,
            registry_service=resolved_registry,
        )
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
        registry_service=resolved_registry,
        polygon_http=resolved_polygon_http,
        polygon_historical=resolved_polygon_historical,
        polygon_realtime=resolved_polygon_realtime,
        finnhub_http=resolved_finnhub_http,
        finnhub_reference=resolved_finnhub_reference,
        finnhub_fundamentals=resolved_finnhub_fundamentals,
    )
