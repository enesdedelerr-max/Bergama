"""Market Data Orchestrator pipeline (#305).

Accepts CanonicalMarketEvent only.

validate → PIT → quality → per-stream acquire → dedup reserve → routing →
bounded in-flight admission → PublishPort → dedup commit/release →
per-stream release

No provider SDK, Kafka, durable queue, scheduler, or EventEnvelope coupling.
``aclose()`` closes internal process-local state only (no background tasks).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import timedelta
from time import perf_counter
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
from app.market_data.orchestrator.errors import (
    OrchestratorClosedError,
    OrchestratorConfigurationError,
)
from app.market_data.orchestrator.metrics import OrchestratorMetrics
from app.market_data.orchestrator.policies import TERMINAL_DECISIONS, PipelineDecision
from app.market_data.orchestrator.ports import DryRunPublishPort, PublishPort
from app.market_data.orchestrator.sequencing import PerStreamSequencer, StreamLease
from app.market_data.orchestrator.stages import (
    apply_sequence,
    build_terminal_audit,
    finalize_decision,
    initial_context,
    mark_accepted,
    run_dedup_stage,
    run_pit_stage,
    run_quality_stage,
    run_routing_stage,
    run_validation_stage,
)

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ProcessResult:
    """Terminal result of processing one canonical event."""

    decision: PipelineDecision
    context: PipelineContext

    @property
    def correlation_id(self) -> str | None:
        return self.context.correlation_id


@dataclass(slots=True)
class MarketDataOrchestrator:
    """Application-scoped canonical event pipeline."""

    settings: OrchestratorSettings
    clock: Clock
    publish_port: PublishPort
    audit_sink: AuditSink = field(default_factory=InMemoryAuditSink)
    metrics: OrchestratorMetrics = field(default_factory=OrchestratorMetrics)
    _dedup: BoundedDedupStore = field(init=False, repr=False)
    _admission: InFlightAdmissionController = field(init=False, repr=False)
    _sequencer: PerStreamSequencer = field(init=False, repr=False)
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
        self._sequencer = PerStreamSequencer()

    @property
    def pipeline_id(self) -> str:
        return self.settings.pipeline_name

    @property
    def closed(self) -> bool:
        return self._closed

    def aclose_sync(self) -> None:
        """Close process-local state. Idempotent. No background tasks to cancel."""
        if self._closed:
            return
        self._closed = True
        self._admission.clear()
        self._dedup.clear()
        self._sequencer.clear()
        self.audit_sink.clear()
        self.metrics.clear()

    async def aclose(self) -> None:
        self.aclose_sync()

    async def process(
        self,
        event: CanonicalMarketEvent,
        *,
        correlation_id: str | None = None,
    ) -> ProcessResult:
        """Process a single canonical event through the full pipeline."""
        if self._closed:
            raise OrchestratorClosedError("orchestrator.closed")

        context = initial_context(event, clock=self.clock, correlation_id=correlation_id)
        context = run_validation_stage(context, pipeline_id=self.pipeline_id)
        if context.decision in TERMINAL_DECISIONS:
            return self._finish(context)

        context = run_pit_stage(context, pipeline_id=self.pipeline_id)
        if context.decision in TERMINAL_DECISIONS:
            return self._finish(context)

        context = run_quality_stage(context)

        lease: StreamLease | None = None
        reserved = False
        dedup_key: str | None = None
        admitted = False
        try:
            lease = await self._sequencer.acquire(event)
            context = apply_sequence(context, info=lease.info)

            context, reserve = await run_dedup_stage(context, store=self._dedup)
            if context.decision in TERMINAL_DECISIONS:
                return self._finish(context)

            reserved = reserve is not None and reserve.outcome is DedupReserveOutcome.RESERVED
            dedup_key = context.dedup_key
            context = run_routing_stage(context)

            try:
                await self._admission.acquire()
            except AdmissionTimeoutError:
                if reserved and dedup_key is not None:
                    await self._dedup.release(dedup_key)
                context = finalize_decision(
                    context,
                    decision=PipelineDecision.BUFFER_OVERFLOW,
                    reason_code="admission_timeout",
                    error_type="AdmissionTimeoutError",
                )
                return self._finish(context)

            admitted = True
            self.metrics.in_flight_current += 1
            context = mark_accepted(context)
            self.metrics.admitted_total += 1

            routing_key = context.routing_key
            if routing_key is None:
                msg = "routing_key missing after routing stage"
                raise RuntimeError(msg)

            if self.settings.dry_run:
                # Explicit dry-run — never report PUBLISHED even if a sink is invoked.
                await self.publish_port.publish(
                    context.event,
                    routing_key=routing_key,
                    context=context,
                )
                if reserved and dedup_key is not None:
                    await self._dedup.release(dedup_key)
                context = finalize_decision(
                    context,
                    decision=PipelineDecision.DRY_RUN,
                    reason_code="dry_run",
                )
                return self._finish(context)

            started = perf_counter()
            try:
                result = await self.publish_port.publish(
                    context.event,
                    routing_key=routing_key,
                    context=context,
                )
            except Exception as exc:
                logger.error(
                    "publish port raised",
                    exc_info=True,
                    extra=structured_extra(
                        event="market_data.orchestrator.publish_error",
                        source="market_data.orchestrator",
                        detail=type(exc).__name__,
                    ),
                )
                if reserved and dedup_key is not None:
                    await self._dedup.release(dedup_key)
                context = finalize_decision(
                    context,
                    decision=PipelineDecision.PUBLISH_FAILED,
                    reason_code="publish_raised",
                    error_type=type(exc).__name__,
                )
                return self._finish(context)
            finally:
                latency_ms = (perf_counter() - started) * 1000.0
                self.metrics.record_publish_latency_ms(latency_ms)

            if not result.succeeded:
                if reserved and dedup_key is not None:
                    await self._dedup.release(dedup_key)
                context = finalize_decision(
                    context,
                    decision=PipelineDecision.PUBLISH_FAILED,
                    reason_code="publish_not_succeeded",
                    error_type="PublishResult",
                    sink_message_id=result.sink_message_id,
                )
                return self._finish(context)

            if reserved and dedup_key is not None:
                await self._dedup.commit(dedup_key, now=self.clock.now())
            context = finalize_decision(
                context,
                decision=PipelineDecision.PUBLISHED,
                reason_code="published",
                sink_message_id=result.sink_message_id,
            )
            return self._finish(context)
        finally:
            if admitted:
                self._admission.release()
                self.metrics.in_flight_current = max(0, self.metrics.in_flight_current - 1)
            if lease is not None:
                await lease.release()

    async def process_batch(
        self,
        events: Sequence[CanonicalMarketEvent],
        *,
        correlation_id: str | None = None,
    ) -> list[ProcessResult]:
        """Process events in given submission order — never globally sorted."""
        results: list[ProcessResult] = []
        for event in events:
            results.append(await self.process(event, correlation_id=correlation_id))
        return results

    def _finish(self, context: PipelineContext) -> ProcessResult:
        decision = context.decision
        if decision not in TERMINAL_DECISIONS:
            msg = f"non-terminal decision at finish: {decision!r}"
            raise RuntimeError(msg)

        completed_at = self.clock.now()
        error_type = context.metadata.get("error_type")
        sink_message_id = context.metadata.get("sink_message_id")
        record = build_terminal_audit(
            context,
            pipeline_id=self.pipeline_id,
            decision=decision,
            reason_code=context.reason or decision.value,
            completed_at=completed_at,
            error_type=error_type,
            sink_message_id=sink_message_id,
        )
        # Exactly one terminal audit entry for this result.
        self.audit_sink.record(record)
        context = context.evolve(audit=(record,))

        if decision is PipelineDecision.PUBLISHED:
            self.metrics.published_total += 1
        elif decision is PipelineDecision.DRY_RUN:
            self.metrics.dry_run_total += 1
        elif decision is PipelineDecision.DUPLICATE_SUPPRESSED:
            self.metrics.duplicate_suppressed_total += 1
        elif decision is PipelineDecision.REJECTED_VALIDATION:
            self.metrics.rejected_validation_total += 1
        elif decision is PipelineDecision.REJECTED_PIT:
            self.metrics.rejected_pit_total += 1
        elif decision is PipelineDecision.BUFFER_OVERFLOW:
            self.metrics.admission_overflow_total += 1
        elif decision is PipelineDecision.PUBLISH_FAILED:
            self.metrics.publish_failed_total += 1

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
        return ProcessResult(decision=decision, context=context)


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
        "stream_count": len(orchestrator._sequencer),
    }
