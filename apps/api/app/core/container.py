"""Explicit application-scoped dependency container (Issues #206–#209 / #302–#304D)."""

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
from app.infrastructure.benzinga.http import BenzingaHttpClient
from app.infrastructure.benzinga.news import BenzingaNewsConnector
from app.infrastructure.finnhub.fundamentals import FinnhubFundamentalsConnector
from app.infrastructure.finnhub.http import FinnhubHttpClient
from app.infrastructure.finnhub.reference import FinnhubReferenceConnector
from app.infrastructure.fred.http import FredHttpClient
from app.infrastructure.fred.observations import FredObservationsConnector
from app.infrastructure.fred.series import FredSeriesConnector
from app.infrastructure.kafka.market_data_publish import KafkaPublishAdapter
from app.infrastructure.kafka.runtime import KafkaRuntime, build_kafka_runtime
from app.infrastructure.polygon.historical import PolygonHistoricalConnector
from app.infrastructure.polygon.http import PolygonHttpClient
from app.infrastructure.polygon.realtime import PolygonRealtimeConnector
from app.infrastructure.sec.http import SecHttpClient
from app.infrastructure.sec.submissions import SecSubmissionsConnector
from app.market_data.orchestrator.errors import OrchestratorConfigurationError
from app.market_data.orchestrator.pipeline import (
    MarketDataOrchestrator,
    build_market_data_orchestrator,
)
from app.market_data.orchestrator.ports import PublishPort
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
    fred_http: FredHttpClient | None
    fred_series: FredSeriesConnector | None
    fred_observations: FredObservationsConnector | None
    sec_http: SecHttpClient | None
    sec_submissions: SecSubmissionsConnector | None
    benzinga_http: BenzingaHttpClient | None
    benzinga_news: BenzingaNewsConnector | None
    market_data_orchestrator: MarketDataOrchestrator | None
    _exit_stack: AsyncExitStack = field(default_factory=AsyncExitStack, repr=False, compare=False)
    _closed: bool = field(default=False, init=False, repr=False, compare=False)

    async def aclose(self) -> None:
        """Release owned async resources. Idempotent."""
        if self._closed:
            return
        self._closed = True
        try:
            await self.registry_service.close()
            # Orchestrator before Kafka so in-flight PublishPort work finishes
            # before the producer is stopped (#306).
            if self.market_data_orchestrator is not None:
                await self.market_data_orchestrator.aclose()
            if self.kafka_runtime is not None:
                await self.kafka_runtime.stop()
            if self.polygon_realtime is not None:
                await self.polygon_realtime.aclose()
            if self.polygon_http is not None:
                await self.polygon_http.aclose()
            if self.finnhub_http is not None:
                await self.finnhub_http.aclose()
            if self.fred_http is not None:
                await self.fred_http.aclose()
            if self.sec_http is not None:
                await self.sec_http.aclose()
            if self.benzinga_http is not None:
                await self.benzinga_http.aclose()
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
    fred_http: FredHttpClient | None = None,
    fred_series: FredSeriesConnector | None = None,
    fred_observations: FredObservationsConnector | None = None,
    sec_http: SecHttpClient | None = None,
    sec_submissions: SecSubmissionsConnector | None = None,
    benzinga_http: BenzingaHttpClient | None = None,
    benzinga_news: BenzingaNewsConnector | None = None,
    market_data_orchestrator: MarketDataOrchestrator | None = None,
    publish_port: PublishPort | None = None,
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

    resolved_fred_http: FredHttpClient | None
    resolved_fred_series: FredSeriesConnector | None
    resolved_fred_observations: FredObservationsConnector | None
    if fred_http is not None:
        resolved_fred_http = fred_http
        resolved_fred_series = (
            fred_series
            if fred_series is not None
            else FredSeriesConnector(fred_http, clock=resolved_clock)
        )
        resolved_fred_observations = (
            fred_observations
            if fred_observations is not None
            else FredObservationsConnector(fred_http, clock=resolved_clock)
        )
    elif settings.fred.enabled:
        resolved_fred_http = FredHttpClient(settings.fred)
        resolved_fred_series = FredSeriesConnector(
            resolved_fred_http,
            clock=resolved_clock,
        )
        resolved_fred_observations = FredObservationsConnector(
            resolved_fred_http,
            clock=resolved_clock,
        )
    else:
        resolved_fred_http = None
        resolved_fred_series = None
        resolved_fred_observations = None

    resolved_sec_http: SecHttpClient | None
    resolved_sec_submissions: SecSubmissionsConnector | None
    if sec_http is not None:
        resolved_sec_http = sec_http
        resolved_sec_submissions = (
            sec_submissions
            if sec_submissions is not None
            else SecSubmissionsConnector(sec_http, clock=resolved_clock)
        )
    elif settings.sec.enabled:
        resolved_sec_http = SecHttpClient(settings.sec)
        resolved_sec_submissions = SecSubmissionsConnector(
            resolved_sec_http,
            clock=resolved_clock,
        )
    else:
        resolved_sec_http = None
        resolved_sec_submissions = None

    resolved_benzinga_http: BenzingaHttpClient | None
    resolved_benzinga_news: BenzingaNewsConnector | None
    if benzinga_http is not None:
        resolved_benzinga_http = benzinga_http
        resolved_benzinga_news = (
            benzinga_news
            if benzinga_news is not None
            else BenzingaNewsConnector(benzinga_http, clock=resolved_clock)
        )
    elif settings.benzinga.enabled:
        resolved_benzinga_http = BenzingaHttpClient(settings.benzinga)
        resolved_benzinga_news = BenzingaNewsConnector(
            resolved_benzinga_http,
            clock=resolved_clock,
        )
    else:
        resolved_benzinga_http = None
        resolved_benzinga_news = None

    resolved_orchestrator: MarketDataOrchestrator | None
    if market_data_orchestrator is not None:
        resolved_orchestrator = market_data_orchestrator
    elif settings.orchestrator.enabled:
        resolved_publish_port: PublishPort | None
        if publish_port is not None:
            # Explicit injection always wins (caller chose to share/own the sink).
            resolved_publish_port = publish_port
        elif settings.orchestrator.dry_run:
            resolved_publish_port = None
        elif settings.orchestrator.publish_backend == "kafka":
            if (
                not settings.kafka.enabled
                or not settings.kafka.producer_enabled
                or resolved_kafka is None
                or resolved_kafka.producer is None
            ):
                raise OrchestratorConfigurationError(
                    "orchestrator.kafka_publish_unavailable",
                    detail=(
                        "publish_backend=kafka requires Kafka enabled with a producer "
                        "(BERGAMA_KAFKA__ENABLED=true, BERGAMA_KAFKA__PRODUCER_ENABLED=true)"
                    ),
                )
            resolved_publish_port = KafkaPublishAdapter(
                producer=resolved_kafka.producer,
                topic_registry=topic_registry,
                clock=resolved_clock,
            )
        else:
            raise OrchestratorConfigurationError("orchestrator.publish_port_required")
        resolved_orchestrator = build_market_data_orchestrator(
            settings.orchestrator,
            clock=resolved_clock,
            publish_port=resolved_publish_port,
        )
    else:
        resolved_orchestrator = None

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
        fred_http=resolved_fred_http,
        fred_series=resolved_fred_series,
        fred_observations=resolved_fred_observations,
        sec_http=resolved_sec_http,
        sec_submissions=resolved_sec_submissions,
        benzinga_http=resolved_benzinga_http,
        benzinga_news=resolved_benzinga_news,
        market_data_orchestrator=resolved_orchestrator,
    )
