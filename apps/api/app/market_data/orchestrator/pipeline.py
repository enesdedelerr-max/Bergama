"""Market Data Orchestrator pipeline (#305).

Accepts CanonicalMarketEvent only. Pipeline:

validate → PIT → quality → dedup reserve → ordering → routing →
bounded in-flight admission → PublishPort → dedup commit/release

No provider SDK, Kafka, durable buffer, or scheduler.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from app.core.clock import Clock
from app.core.logging import get_logger, structured_extra
from app.core.orchestrator_settings import OrchestratorSettings
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.orchestrator.admission import (
    AdmissionTimeoutError,
    InFlightAdmissionController,
)
from app.market_data.orchestrator.audit import AuditSink, InMemoryAuditSink
from app.market_data.orchestrator.context import PipelineContext
from app.market_data.orchestrator.dedup import BoundedDedupStore, DedupReserveOutcome
from app.market_data.orchestrator.errors import OrchestratorConfigurationError
from app.market_data.orchestrator.ordering import OrderingTracker
from app.market_data.orchestrator.policies import TERMINAL_DECISIONS, PipelineDecision
from app.market_data.orchestrator.ports import DryRunPublishPort, PublishPort
from app.market_data.orchestrator.stages import (
    finalize_buffer_overflow,
    finalize_dry_run,
    finalize_publish_failed,
    finalize_published,
    initial_context,
    mark_accepted,
    run_dedup_stage,
    run_ordering_stage,
    run_pit_stage,
    run_quality_stage,
    run_routing_stage,
    run_validation_stage,
)

logger = get_logger(__name__)


@dataclass(slots=True)
class PipelineMetrics:
    """In-process counters for orchestrator observability."""

    accepted: int = 0
    published: int = 0
    duplicate_suppressed: int = 0
    rejected_validation: int = 0
    rejected_pit: int = 0
    buffer_overflow: int = 0
    publish_failed: int = 0
    dry_run: int = 0
    processed: int = 0

    def snapshot(self) -> Mapping[str, int]:
        return {
            "accepted": self.accepted,
            "published": self.published,
            "duplicate_suppressed": self.duplicate_suppressed,
            "rejected_validation": self.rejected_validation,
            "rejected_pit": self.rejected_pit,
            "buffer_overflow": self.buffer_overflow,
            "publish_failed": self.publish_failed,
            "dry_run": self.dry_run,
            "processed": self.processed,
        }


@dataclass(slots=True)
class MarketDataOrchestrator:
    """Application-scoped canonical event pipeline."""

    settings: OrchestratorSettings
    clock: Clock
    publish_port: PublishPort
    audit_sink: AuditSink = field(default_factory=InMemoryAuditSink)
    metrics: PipelineMetrics = field(default_factory=PipelineMetrics)
    _dedup: BoundedDedupStore = field(init=False, repr=False)
    _admission: InFlightAdmissionController = field(init=False, repr=False)
    _ordering: OrderingTracker = field(init=False, repr=False)
    _closed: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.settings.enabled:
            raise OrchestratorConfigurationError(
                "orchestrator.disabled",
                detail="MarketDataOrchestrator requires settings.enabled=true",
            )
        self._dedup = BoundedDedupStore(
            ttl=timedelta(seconds=self.settings.dedup_ttl_seconds),
            max_entries=self.settings.dedup_max_entries,
        )
        self._admission = InFlightAdmissionController(
            max_in_flight=self.settings.max_in_flight,
            timeout_seconds=self.settings.admission_timeout_seconds,
        )
        self._ordering = OrderingTracker()

    @property
    def pipeline_id(self) -> str:
        return self.settings.pipeline_name

    @property
    def closed(self) -> bool:
        return self._closed

    def aclose_sync(self) -> None:
        """Release in-memory state. Idempotent."""
        if self._closed:
            return
        self._closed = True
        self._admission.clear()
        self._dedup.clear()
        self._ordering.clear()
        self.audit_sink.clear()

    async def aclose(self) -> None:
        self.aclose_sync()

    async def process(
        self,
        event: CanonicalMarketEvent,
        *,
        correlation_id: str | None = None,
    ) -> PipelineContext:
        """Process a single canonical event through the full pipeline."""
        if self._closed:
            msg = "orchestrator is closed"
            raise RuntimeError(msg)

        context = initial_context(event, clock=self.clock, correlation_id=correlation_id)
        context = run_validation_stage(context, pipeline_id=self.pipeline_id)
        context = run_pit_stage(context, pipeline_id=self.pipeline_id)
        context = run_quality_stage(context)
        context, reserve = await run_dedup_stage(
            context,
            pipeline_id=self.pipeline_id,
            store=self._dedup,
        )
        context = run_ordering_stage(context, tracker=self._ordering)
        context = run_routing_stage(context)

        if context.decision in TERMINAL_DECISIONS:
            self._observe(context)
            return context

        reserved = reserve is not None and reserve.outcome is DedupReserveOutcome.RESERVED
        dedup_key = context.dedup_key

        try:
            await self._admission.acquire()
        except AdmissionTimeoutError as exc:
            if reserved and dedup_key is not None:
                await self._dedup.release(dedup_key)
            overflow = finalize_buffer_overflow(
                context,
                pipeline_id=self.pipeline_id,
                detail=str(exc),
            )
            self._observe(overflow)
            return overflow

        context = mark_accepted(context, pipeline_id=self.pipeline_id)
        # Intermediate ACCEPTED is counted separately from terminal outcomes.
        self.metrics.accepted += 1

        assert context.routing_key is not None
        try:
            result = await self.publish_port.publish(
                context.event,
                routing_key=context.routing_key,
                context=context,
            )
        except Exception as exc:
            logger.error(
                "publish port raised",
                exc_info=True,
                extra=structured_extra(
                    event="market_data.orchestrator.publish_error",
                    source="market_data.orchestrator",
                    detail=str(exc),
                ),
            )
            if reserved and dedup_key is not None:
                await self._dedup.release(dedup_key)
            failed = finalize_publish_failed(
                context,
                pipeline_id=self.pipeline_id,
                detail=f"publish raised: {exc}",
            )
            self._observe(failed)
            return failed
        finally:
            self._admission.release()

        if result.mode == "dry_run":
            if reserved and dedup_key is not None:
                await self._dedup.release(dedup_key)
            dry = finalize_dry_run(
                context,
                pipeline_id=self.pipeline_id,
                detail=result.detail or "dry_run",
            )
            self._observe(dry)
            return dry

        if not result.ok:
            if reserved and dedup_key is not None:
                await self._dedup.release(dedup_key)
            failed = finalize_publish_failed(
                context,
                pipeline_id=self.pipeline_id,
                detail=result.detail or "publish returned ok=false",
            )
            self._observe(failed)
            return failed

        if reserved and dedup_key is not None:
            await self._dedup.commit(dedup_key, now=self.clock.now())
        published = finalize_published(context, pipeline_id=self.pipeline_id)
        self._observe(published)
        return published

    async def process_batch(
        self,
        events: Sequence[CanonicalMarketEvent],
        *,
        correlation_id: str | None = None,
    ) -> list[PipelineContext]:
        """Process events in given order — never globally sorted."""
        results: list[PipelineContext] = []
        for event in events:
            results.append(await self.process(event, correlation_id=correlation_id))
        return results

    def _observe(self, context: PipelineContext) -> None:
        self.metrics.processed += 1
        decision = context.decision
        if decision is PipelineDecision.PUBLISHED:
            self.metrics.published += 1
        elif decision is PipelineDecision.DUPLICATE_SUPPRESSED:
            self.metrics.duplicate_suppressed += 1
        elif decision is PipelineDecision.REJECTED_VALIDATION:
            self.metrics.rejected_validation += 1
        elif decision is PipelineDecision.REJECTED_PIT:
            self.metrics.rejected_pit += 1
        elif decision is PipelineDecision.BUFFER_OVERFLOW:
            self.metrics.buffer_overflow += 1
        elif decision is PipelineDecision.PUBLISH_FAILED:
            self.metrics.publish_failed += 1
        elif decision is PipelineDecision.DRY_RUN:
            self.metrics.dry_run += 1

        if context.audit:
            self.audit_sink.record(context.audit[-1])

        logger.info(
            "market data orchestrator decision",
            extra=structured_extra(
                event="market_data.orchestrator.decision",
                source="market_data.orchestrator",
                pipeline_id=self.pipeline_id,
                decision=decision.value,
                routing_key=context.routing_key,
                dedup_key=context.dedup_key,
                idempotency_key=context.idempotency_key,
                correlation_id=context.correlation_id,
                reason=context.reason,
            ),
        )


def build_market_data_orchestrator(
    settings: OrchestratorSettings,
    *,
    clock: Clock,
    publish_port: PublishPort | None = None,
    audit_sink: AuditSink | None = None,
) -> MarketDataOrchestrator:
    """Construct an application-scoped orchestrator.

    Requires ``settings.enabled=true``. A PublishPort must be supplied unless
    ``settings.dry_run=true``, in which case an explicit DryRunPublishPort is used.
    """
    if not settings.enabled:
        raise OrchestratorConfigurationError(
            "orchestrator.disabled",
            detail="cannot construct MarketDataOrchestrator while disabled",
        )

    resolved_port: PublishPort
    if publish_port is not None:
        resolved_port = publish_port
    elif settings.dry_run:
        resolved_port = DryRunPublishPort(clock=clock)
    else:
        raise OrchestratorConfigurationError("orchestrator.publish_port_required")

    sink: AuditSink = audit_sink if audit_sink is not None else InMemoryAuditSink()
    return MarketDataOrchestrator(
        settings=settings,
        clock=clock,
        publish_port=resolved_port,
        audit_sink=sink,
    )


def orchestrator_safe_summary(orchestrator: MarketDataOrchestrator) -> dict[str, Any]:
    admission = orchestrator._admission.stats()
    return {
        **orchestrator.settings.safe_summary(),
        "closed": orchestrator.closed,
        "metrics": dict(orchestrator.metrics.snapshot()),
        "admission": {
            "max_in_flight": admission.max_in_flight,
            "in_flight": admission.in_flight,
            "overflow_count": admission.overflow_count,
        },
        "dedup_size": len(orchestrator._dedup),
    }
