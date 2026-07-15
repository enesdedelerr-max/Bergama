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
from app.infrastructure.backfill.benzinga import BenzingaBackfillSource
from app.infrastructure.backfill.file_checkpoint import FileBackfillCheckpointStore
from app.infrastructure.backfill.finnhub import FinnhubRefreshSource
from app.infrastructure.backfill.fred import FredBackfillSource
from app.infrastructure.backfill.polygon import PolygonHistoricalBackfillSource
from app.infrastructure.backfill.sec import SecRefreshSource
from app.infrastructure.benzinga.http import BenzingaHttpClient
from app.infrastructure.benzinga.news import BenzingaNewsConnector
from app.infrastructure.finnhub.fundamentals import FinnhubFundamentalsConnector
from app.infrastructure.finnhub.http import FinnhubHttpClient
from app.infrastructure.finnhub.reference import FinnhubReferenceConnector
from app.infrastructure.fred.http import FredHttpClient
from app.infrastructure.fred.observations import FredObservationsConnector
from app.infrastructure.fred.series import FredSeriesConnector
from app.infrastructure.iceberg.catalog import build_catalog, require_tables_present
from app.infrastructure.iceberg.consumer import IcebergWriterRuntime
from app.infrastructure.iceberg.health import IcebergWriterHealthCheck
from app.infrastructure.iceberg.replay_source import IcebergReplaySource
from app.infrastructure.iceberg.runtime import build_iceberg_writer_runtime
from app.infrastructure.kafka.market_data_publish import KafkaPublishAdapter
from app.infrastructure.kafka.runtime import KafkaRuntime, build_kafka_runtime
from app.infrastructure.polygon.historical import PolygonHistoricalConnector
from app.infrastructure.polygon.http import PolygonHttpClient
from app.infrastructure.polygon.realtime import PolygonRealtimeConnector
from app.infrastructure.replay.file_checkpoint import FileCheckpointStore
from app.infrastructure.sec.http import SecHttpClient
from app.infrastructure.sec.submissions import SecSubmissionsConnector
from app.market_data.backfill.engine import (
    BackfillEngine,
    StaticSourceRegistry,
    build_backfill_engine,
)
from app.market_data.backfill.ports import BackfillSource
from app.market_data.data_quality import (
    DataQualityHealthCheck,
    DataQualityService,
    InMemoryQuarantinePort,
    QualityMetrics,
    default_quality_policy,
    load_quality_policy_file,
)
from app.market_data.orchestrator.errors import OrchestratorConfigurationError
from app.market_data.orchestrator.pipeline import (
    MarketDataOrchestrator,
    build_market_data_orchestrator,
)
from app.market_data.orchestrator.ports import PublishPort
from app.market_data.replay.engine import ReplayEngine, build_replay_engine
from app.registry.service import RegistryService
from app.services.token_service import TokenService
from app.strategy.engine import StrategyEngine, build_strategy_engine
from app.strategy.reference import NoOpStrategy, NoOpStrategyConfig
from app.strategy.registry import StrategyRegistry

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
    data_quality_service: DataQualityService | None
    iceberg_writer_runtime: IcebergWriterRuntime | None
    replay_engine: ReplayEngine | None
    backfill_engine: BackfillEngine | None
    strategy_engine: StrategyEngine | None
    _exit_stack: AsyncExitStack = field(default_factory=AsyncExitStack, repr=False, compare=False)
    _closed: bool = field(default=False, init=False, repr=False, compare=False)

    async def aclose(self) -> None:
        """Release owned async resources. Idempotent."""
        if self._closed:
            return
        self._closed = True
        try:
            await self.registry_service.close()
            # Orchestrator before writers/Kafka so in-flight PublishPort work finishes.
            if self.market_data_orchestrator is not None:
                await self.market_data_orchestrator.aclose()
            if self.data_quality_service is not None:
                await self.data_quality_service.aclose()
            # Replay Engine owns its source/checkpoint only — never starts on aclose (#308).
            if self.replay_engine is not None:
                await self.replay_engine.aclose()
            # Backfill owns checkpoint store only; adapters do not close shared connectors (#309).
            if self.backfill_engine is not None:
                await self.backfill_engine.aclose()
            if self.strategy_engine is not None:
                await self.strategy_engine.aclose()
            # Iceberg writer: stop intake → flush → snapshots → offsets → consumer → catalog
            # before shared Kafka runtime is stopped (#307).
            if self.iceberg_writer_runtime is not None:
                await self.iceberg_writer_runtime.aclose()
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
    data_quality_service: DataQualityService | None = None,
    iceberg_writer_runtime: IcebergWriterRuntime | None = None,
    replay_engine: ReplayEngine | None = None,
    backfill_engine: BackfillEngine | None = None,
    strategy_engine: StrategyEngine | None = None,
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

    resolved_quality: DataQualityService | None
    if data_quality_service is not None:
        resolved_quality = data_quality_service
    elif settings.data_quality.enabled:
        if settings.data_quality.policy_file is not None:
            quality_policy = load_quality_policy_file(
                settings.data_quality.policy_file,
                max_file_size_bytes=settings.data_quality.policy_max_file_bytes,
            )
        else:
            quality_policy = default_quality_policy(
                observe_only=settings.data_quality.observe_only,
                reject_on_error=settings.data_quality.reject_on_error,
                halt_on_critical=settings.data_quality.halt_on_critical,
                quarantine_on_error=settings.data_quality.quarantine_enabled,
                aggregation_window_seconds=settings.data_quality.aggregation_window_seconds,
                max_problem_dimensions=settings.data_quality.max_problem_dimensions,
            )
        quarantine_port = (
            InMemoryQuarantinePort()
            if settings.data_quality.quarantine_enabled
            and not settings.environment.is_production_like
            else None
        )
        resolved_quality = DataQualityService(
            policy=quality_policy,
            clock=resolved_clock,
            metrics=QualityMetrics(
                max_tracked_instruments=settings.data_quality.max_tracked_instruments,
                max_problem_dimensions=settings.data_quality.max_problem_dimensions,
            ),
            quarantine_port=quarantine_port,
            enabled=True,
            required=settings.data_quality.required,
            readiness_fail_on_critical_halt=settings.data_quality.readiness_fail_on_critical_halt,
        )
    elif settings.data_quality.required:
        raise OrchestratorConfigurationError(
            "data_quality.required_disabled",
            detail="data quality required but disabled",
        )
    else:
        resolved_quality = None

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
            data_quality_service=resolved_quality,
        )
    else:
        resolved_orchestrator = None

    # Iceberg writer construction performs catalog/table metadata checks only —
    # no appends and no Kafka consume until runtime.start() (#307).
    resolved_iceberg: IcebergWriterRuntime | None
    if iceberg_writer_runtime is not None:
        resolved_iceberg = iceberg_writer_runtime
    elif settings.iceberg_writer.enabled:
        resolved_iceberg = build_iceberg_writer_runtime(
            settings,
            clock=resolved_clock,
            topic_registry=topic_registry,
        )
    else:
        resolved_iceberg = None

    # Replay Engine: construct when enabled/injected. Never starts a run here (#308).
    resolved_replay: ReplayEngine | None
    if replay_engine is not None:
        resolved_replay = replay_engine
    elif settings.replay.enabled:
        replay_catalog = build_catalog(settings.iceberg_writer)
        replay_source = IcebergReplaySource(
            replay_catalog,
            settings.iceberg_writer,
            owns_catalog=True,
        )
        checkpoint_store = None
        if settings.replay.checkpoint_enabled:
            if settings.replay.checkpoint_directory is None:
                raise OrchestratorConfigurationError(
                    "replay.checkpoint_directory_required",
                    detail="checkpoint_directory required when checkpoint_enabled",
                )
            checkpoint_store = FileCheckpointStore(settings.replay.checkpoint_directory)
        resolved_replay = build_replay_engine(
            settings.replay,
            clock=resolved_clock,
            source=replay_source,
            checkpoint_store=checkpoint_store,
        )
    else:
        resolved_replay = None

    # Backfill Engine: construct when enabled/injected. Never starts a run here (#309).
    resolved_backfill: BackfillEngine | None
    if backfill_engine is not None:
        resolved_backfill = backfill_engine
    elif settings.backfill.enabled:
        sources: dict[tuple[str, str], BackfillSource] = {}
        if resolved_polygon_historical is not None:
            sources[("polygon", "aggregates")] = PolygonHistoricalBackfillSource(
                resolved_polygon_historical,
                settings.backfill,
                owns_connector=False,
            )
        if resolved_fred_observations is not None:
            sources[("fred", "observations")] = FredBackfillSource(
                resolved_fred_observations,
                settings.backfill,
                owns_connector=False,
            )
        if resolved_benzinga_news is not None:
            sources[("benzinga", "news")] = BenzingaBackfillSource(
                resolved_benzinga_news,
                settings.backfill,
                owns_connector=False,
            )
        if resolved_finnhub_reference is not None or resolved_finnhub_fundamentals is not None:
            finnhub_src = FinnhubRefreshSource(
                reference=resolved_finnhub_reference,
                fundamentals=resolved_finnhub_fundamentals,
                settings=settings.backfill,
                owns_connector=False,
            )
            sources[("finnhub", "profile_refresh")] = finnhub_src
            sources[("finnhub", "fundamentals_refresh")] = finnhub_src
            sources[("finnhub", "both_refresh")] = finnhub_src
        if resolved_sec_submissions is not None:
            sources[("sec", "recent_filings")] = SecRefreshSource(
                resolved_sec_submissions,
                settings.backfill,
                owns_connector=False,
            )
        backfill_checkpoint = None
        if settings.backfill.checkpoint_enabled:
            if settings.backfill.checkpoint_directory is None:
                raise OrchestratorConfigurationError(
                    "backfill.checkpoint_directory_required",
                    detail="checkpoint_directory required when checkpoint_enabled",
                )
            backfill_checkpoint = FileBackfillCheckpointStore(
                settings.backfill.checkpoint_directory
            )
        resolved_backfill = build_backfill_engine(
            settings.backfill,
            clock=resolved_clock,
            source_registry=StaticSourceRegistry(sources=sources),
            checkpoint_store=backfill_checkpoint,
        )
    else:
        resolved_backfill = None

    # Strategy Engine: construct when enabled/injected. Never evaluates on startup (#401).
    resolved_strategy_engine: StrategyEngine | None
    if strategy_engine is not None:
        resolved_strategy_engine = strategy_engine
    elif settings.strategy.enabled:
        strategy_registry = StrategyRegistry()
        if settings.strategy.register_reference_strategy:
            strategy_registry.register(
                "noop",
                lambda _identity, config: NoOpStrategy(
                    config if isinstance(config, NoOpStrategyConfig) else NoOpStrategyConfig()
                ),
            )
        resolved_strategy_engine = build_strategy_engine(
            clock=resolved_clock,
            registry=strategy_registry,
            decision_port=None,
            max_strategies_per_session=settings.strategy.max_strategies_per_session,
            max_seen_inputs_per_session=settings.strategy.max_seen_inputs_per_session,
            audit_max_records=settings.strategy.audit_max_records,
        )
    else:
        resolved_strategy_engine = None

    if health_checks is not None:
        resolved_checks: tuple[HealthCheck, ...] = tuple(health_checks)
    else:
        base_checks: list[HealthCheck] = list(
            build_default_health_checks(
                settings,
                kafka_runtime=resolved_kafka,
                registry_service=resolved_registry,
            )
        )
        if settings.iceberg_writer.enabled and resolved_iceberg is not None:
            iceberg_runtime = resolved_iceberg

            def _catalog_probe() -> None:
                iceberg_runtime.catalog.list_namespaces()

            def _tables_probe() -> None:
                require_tables_present(
                    iceberg_runtime.catalog,
                    settings.iceberg_writer,
                )

            base_checks.append(
                IcebergWriterHealthCheck(
                    settings=settings.iceberg_writer,
                    timeout_seconds=settings.health_check_timeout_seconds,
                    catalog_probe=_catalog_probe,
                    tables_probe=_tables_probe,
                    worker_started=lambda: iceberg_runtime.started,
                )
            )
        if resolved_quality is not None:
            base_checks.append(
                DataQualityHealthCheck(
                    service=resolved_quality,
                    timeout_seconds=settings.health_check_timeout_seconds,
                )
            )
        resolved_checks = tuple(base_checks)
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
        data_quality_service=resolved_quality,
        iceberg_writer_runtime=resolved_iceberg,
        replay_engine=resolved_replay,
        backfill_engine=resolved_backfill,
        strategy_engine=resolved_strategy_engine,
    )
