"""Historical Backfill Pipeline engine (#309).

Flow:
  BackfillRequest → BackfillSource → slices → connector events →
  isolated MarketDataOrchestrator → explicit PublishPort or none →
  checkpoint → audit

No raw httpx. No Kafka/Iceberg writes. No ReplayEngine coupling.
No silent production KafkaPublishAdapter. Sequential MVP slices.
At-least-once publish only — no exactly-once claim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.core.backfill_settings import BackfillSettings
from app.core.clock import Clock
from app.core.logging import get_logger, structured_extra
from app.core.orchestrator_settings import OrchestratorSettings
from app.market_data.backfill.audit import (
    BackfillEventAudit,
    BackfillRunAudit,
    BackfillSliceAudit,
    InMemoryBackfillAuditSink,
)
from app.market_data.backfill.checkpoint import BackfillCheckpoint
from app.market_data.backfill.errors import (
    BackfillCancelledError,
    BackfillCheckpointMismatchError,
    BackfillClosedError,
    BackfillCompletedError,
    BackfillDisabledError,
    BackfillError,
    BackfillInvalidRequestError,
    BackfillPitError,
    BackfillSinkFailedError,
    BackfillSinkRequiredError,
    BackfillTruncatedError,
    BackfillValidationError,
)
from app.market_data.backfill.models import (
    BackfillDecision,
    BackfillMode,
    BackfillRequest,
    BackfillRunResult,
    BackfillSinkType,
    BackfillTerminalStatus,
    SliceStatus,
    new_backfill_id,
)
from app.market_data.backfill.policies import (
    AsyncioBackfillSleeper,
    TokenBucketRateLimiter,
    resolve_limits,
    sink_type_for_mode,
)
from app.market_data.backfill.ports import (
    BackfillAuditSink,
    BackfillCheckpointStore,
    BackfillSleeper,
    BackfillSource,
    BackfillSourceRegistry,
)
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.keys import build_idempotency_key
from app.market_data.orchestrator.pipeline import (
    MarketDataOrchestrator,
    build_market_data_orchestrator,
)
from app.market_data.orchestrator.policies import PipelineDecision
from app.market_data.orchestrator.ports import PublishPort
from app.market_data.orchestrator.stages import (
    initial_context,
    run_pit_stage,
    run_quality_stage,
    run_routing_stage,
    run_validation_stage,
)

logger = get_logger(__name__)


@dataclass(slots=True)
class StaticSourceRegistry:
    """Simple registry mapping provider/source_kind to an adapter."""

    sources: dict[tuple[str, str], BackfillSource]

    def resolve(self, request: BackfillRequest) -> BackfillSource:
        key = (request.provider.value, request.source_kind.value)
        try:
            return self.sources[key]
        except KeyError as exc:
            raise BackfillInvalidRequestError(
                detail=f"no source adapter registered for {key[0]}/{key[1]}"
            ) from exc


@dataclass(slots=True)
class BackfillEngine:
    """Application-scoped backfill runner. Explicit ``run()`` only."""

    settings: BackfillSettings
    clock: Clock
    source_registry: BackfillSourceRegistry
    checkpoint_store: BackfillCheckpointStore | None = None
    audit_sink: BackfillAuditSink = field(default_factory=InMemoryBackfillAuditSink)
    sleeper: BackfillSleeper = field(default_factory=AsyncioBackfillSleeper)
    _closed: bool = field(default=False, init=False, repr=False)
    _cancel_requested: bool = field(default=False, init=False, repr=False)
    _owns_checkpoint: bool = field(default=True, repr=False)

    @property
    def closed(self) -> bool:
        return self._closed

    def request_cancel(self) -> None:
        self._cancel_requested = True

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._cancel_requested = True
        if self._owns_checkpoint and self.checkpoint_store is not None:
            await self.checkpoint_store.aclose()
        self.audit_sink.clear()

    async def run(
        self,
        request: BackfillRequest,
        *,
        backfill_id: str | None = None,
        publish_port: PublishPort | None = None,
    ) -> BackfillRunResult:
        if self._closed:
            raise BackfillClosedError()
        if not self.settings.enabled:
            raise BackfillDisabledError(detail="backfill engine is disabled")

        self._cancel_requested = False
        mode = request.mode
        sink_type = _resolve_sink_type(mode, publish_port=publish_port)
        limits = resolve_limits(request, self.settings)
        bid = (backfill_id or request.checkpoint_id or new_backfill_id()).strip()
        if not bid:
            raise BackfillInvalidRequestError(detail="backfill_id must be non-empty")
        fingerprint = request.fingerprint(sink_type=sink_type)
        started_at = self.clock.now()
        source = self.source_registry.resolve(request)

        checkpoint = await self._prepare_checkpoint(
            request=request,
            backfill_id=bid,
            fingerprint=fingerprint,
            started_at=started_at,
        )

        slices = list(source.build_slices(request))
        if len(slices) > self.settings.max_slices:
            from app.market_data.backfill.errors import BackfillUnboundedRequestError

            raise BackfillUnboundedRequestError(
                detail=f"slice count exceeds max_slices={self.settings.max_slices}"
            )

        completed = set(checkpoint.completed_slices)
        pending = [s for s in slices if s.slice_id not in completed]
        # Resume incomplete current slice first if fingerprint matched.
        if (
            checkpoint.current_slice is not None
            and checkpoint.current_slice.slice_id not in completed
        ):
            cur_id = checkpoint.current_slice.slice_id
            pending = [s for s in pending if s.slice_id == cur_id] + [
                s for s in pending if s.slice_id != cur_id
            ]

        resume_slice_id = (
            checkpoint.current_slice.slice_id if checkpoint.current_slice is not None else None
        )
        resume_after_key = checkpoint.last_successful_event_key
        resume_slice_processed = (
            checkpoint.current_slice.processed_count if checkpoint.current_slice is not None else 0
        )

        self.audit_sink.record_run(
            BackfillRunAudit(
                backfill_id=bid,
                provider=request.provider,
                source_kind=request.source_kind,
                mode=mode,
                request_fingerprint=fingerprint,
                selector_summary=request.selector_summary(),
                start_time=request.start_time,
                end_time=request.end_time,
                sink_type=sink_type,
                slice_count=len(slices),
                processed_count=checkpoint.processed_count,
                published_count=checkpoint.published_count,
                failed_count=checkpoint.failed_count,
                started_at=started_at,
                completed_at=None,
                terminal_status=None,
            )
        )

        orchestrator: MarketDataOrchestrator | None = None
        processed = checkpoint.processed_count
        published = checkpoint.published_count
        failed = checkpoint.failed_count
        last_key = checkpoint.last_successful_event_key
        completed_list = list(checkpoint.completed_slices)
        terminal: BackfillTerminalStatus = "failed"
        records_budget = request.max_records - processed

        try:
            if mode is BackfillMode.PUBLISH:
                assert publish_port is not None
                orch_settings = OrchestratorSettings(
                    enabled=True,
                    dry_run=False,
                    publish_backend="none",
                    pipeline_name=f"backfill-{bid[:8]}",
                    max_in_flight=limits.max_in_flight_events,
                    admission_timeout_seconds=0.05,
                )
                orchestrator = build_market_data_orchestrator(
                    orch_settings,
                    clock=self.clock,
                    publish_port=publish_port,
                )
            else:
                orch_settings = OrchestratorSettings(
                    enabled=True,
                    dry_run=True,
                    publish_backend="none",
                    pipeline_name=f"backfill-{bid[:8]}",
                    max_in_flight=limits.max_in_flight_events,
                    admission_timeout_seconds=0.05,
                )
                orchestrator = build_market_data_orchestrator(
                    orch_settings,
                    clock=self.clock,
                )

            rate = TokenBucketRateLimiter(
                events_per_second=limits.events_per_second,
                sleeper=self.sleeper,
            )

            for slice_ in pending:
                if self._cancel_requested:
                    raise BackfillCancelledError(detail="cancel requested")
                if records_budget <= 0:
                    break

                current = slice_.evolve(status="running")
                checkpoint = checkpoint.evolve(
                    current_slice=current,
                    updated_at=self.clock.now(),
                )
                await self._persist(checkpoint)

                events, may_have_more, request_count, cursor = await source.fetch_slice(
                    current,
                    request,
                )
                if may_have_more:
                    self.audit_sink.record_slice(
                        BackfillSliceAudit(
                            backfill_id=bid,
                            slice_id=current.slice_id,
                            start_time=current.start_time,
                            end_time=current.end_time,
                            provider_cursor_summary=dict(cursor),
                            request_count=request_count,
                            event_count=len(events),
                            status="failed",
                            failure_reason="may_have_more",
                        )
                    )
                    raise BackfillTruncatedError(
                        detail=(
                            f"slice {current.slice_id} truncated "
                            "(may_have_more); shrink slice or raise page budget"
                        )
                    )

                ordered = _order_events(list(events), slice_start=current.start_time)
                if records_budget < len(ordered):
                    ordered = ordered[:records_budget]

                skip_until_after = (
                    resume_after_key
                    if (
                        resume_slice_id == current.slice_id
                        and resume_after_key is not None
                        and resume_slice_processed > 0
                    )
                    else None
                )
                prior_slice_processed = (
                    resume_slice_processed if resume_slice_id == current.slice_id else 0
                )
                prior_slice_published = (
                    checkpoint.current_slice.published_count
                    if (
                        checkpoint.current_slice is not None
                        and checkpoint.current_slice.slice_id == current.slice_id
                    )
                    else 0
                )

                slice_processed = prior_slice_processed
                slice_published = prior_slice_published
                for event in ordered:
                    event_key = build_idempotency_key(event)
                    if skip_until_after is not None:
                        if event_key == skip_until_after:
                            skip_until_after = None
                        continue

                    if self._cancel_requested:
                        raise BackfillCancelledError(detail="cancel requested")
                    await rate.admit(cancelled=self._cancel_requested)

                    decision, reason, sink_msg = await self._handle_event(
                        event=event,
                        mode=mode,
                        orchestrator=orchestrator,
                        backfill_id=bid,
                    )
                    processed += 1
                    slice_processed += 1
                    records_budget -= 1
                    self.audit_sink.record_event(
                        BackfillEventAudit(
                            backfill_id=bid,
                            idempotency_key=event_key,
                            event_type=event.event_type.value,
                            instrument_key=event.instrument.instrument_key,
                            occurred_at=event.occurred_at,
                            decision=decision,
                            reason=reason,
                            processed_at=self.clock.now(),
                            sink_message_id=sink_msg,
                        )
                    )

                    if decision in {
                        BackfillDecision.REJECTED_VALIDATION,
                        BackfillDecision.REJECTED_PIT,
                        BackfillDecision.SINK_FAILED,
                    }:
                        failed += 1
                        failed_slice = current.evolve(
                            status="failed",
                            processed_count=slice_processed,
                            published_count=slice_published,
                            failed_count=1,
                            provider_cursor=cursor,
                        )
                        checkpoint = checkpoint.evolve(
                            current_slice=failed_slice,
                            processed_count=processed,
                            published_count=published,
                            failed_count=failed,
                            last_successful_event_key=last_key,
                            provider_cursor=cursor,
                            updated_at=self.clock.now(),
                            completed=False,
                        )
                        await self._persist(checkpoint)
                        if decision is BackfillDecision.REJECTED_VALIDATION:
                            raise BackfillValidationError(detail=reason)
                        if decision is BackfillDecision.REJECTED_PIT:
                            raise BackfillPitError(detail=reason)
                        raise BackfillSinkFailedError(detail=reason)

                    if decision is BackfillDecision.PUBLISHED:
                        published += 1
                        slice_published += 1
                    last_key = event_key
                    checkpoint = checkpoint.evolve(
                        current_slice=current.evolve(
                            status="running",
                            processed_count=slice_processed,
                            published_count=slice_published,
                            provider_cursor=cursor,
                        ),
                        processed_count=processed,
                        published_count=published,
                        failed_count=failed,
                        last_successful_event_key=last_key,
                        provider_cursor=cursor,
                        updated_at=self.clock.now(),
                    )
                    await self._persist(checkpoint)

                if skip_until_after is not None:
                    raise BackfillCheckpointMismatchError(
                        detail="resume event key not found in slice results"
                    )

                slice_status: SliceStatus = "empty" if slice_processed == 0 else "completed"
                completed_list.append(current.slice_id)
                self.audit_sink.record_slice(
                    BackfillSliceAudit(
                        backfill_id=bid,
                        slice_id=current.slice_id,
                        start_time=current.start_time,
                        end_time=current.end_time,
                        provider_cursor_summary=dict(cursor),
                        request_count=request_count,
                        event_count=slice_processed,
                        status=slice_status,
                    )
                )
                # Clear last_successful_event_key at slice boundary so the next
                # slice does not incorrectly skip events using a prior-slice key.
                checkpoint = checkpoint.evolve(
                    current_slice=None,
                    completed_slices=tuple(completed_list),
                    processed_count=processed,
                    published_count=published,
                    failed_count=failed,
                    last_successful_event_key=None,
                    provider_cursor=cursor,
                    updated_at=self.clock.now(),
                )
                last_key = None
                await self._persist(checkpoint)
                # Resume skip applies only to the incomplete slice from load time.
                resume_slice_id = None
                resume_after_key = None
                resume_slice_processed = 0

            terminal = "completed_empty" if processed == 0 and failed == 0 else "completed"
            completed_at = self.clock.now()
            final = checkpoint.evolve(
                completed=True,
                completed_at=completed_at,
                terminal_status=terminal,
                updated_at=completed_at,
                current_slice=None,
            )
            await self._persist(final)
            result = BackfillRunResult(
                backfill_id=bid,
                provider=request.provider,
                source_kind=request.source_kind,
                mode=mode,
                request_fingerprint=fingerprint,
                sink_type=sink_type,
                started_at=started_at,
                completed_at=completed_at,
                slice_count=len(slices),
                processed_count=processed,
                published_count=published,
                failed_count=failed,
                terminal_status=terminal,
            )
            self.audit_sink.record_run(
                BackfillRunAudit(
                    backfill_id=bid,
                    provider=request.provider,
                    source_kind=request.source_kind,
                    mode=mode,
                    request_fingerprint=fingerprint,
                    selector_summary=request.selector_summary(),
                    start_time=request.start_time,
                    end_time=request.end_time,
                    sink_type=sink_type,
                    slice_count=len(slices),
                    processed_count=processed,
                    published_count=published,
                    failed_count=failed,
                    started_at=started_at,
                    completed_at=completed_at,
                    terminal_status=terminal,
                )
            )
            logger.info(
                "backfill run completed",
                extra=structured_extra(
                    event="market_data.backfill.completed",
                    source="market_data.backfill",
                    backfill_id=bid,
                    provider=request.provider.value,
                    source_kind=request.source_kind.value,
                    mode=mode.value,
                    processed_count=processed,
                    published_count=published,
                    terminal_status=terminal,
                ),
            )
            return result
        except BackfillError as exc:
            completed_at = self.clock.now()
            fail_status: BackfillTerminalStatus = (
                "cancelled" if isinstance(exc, BackfillCancelledError) else "failed"
            )
            await self._persist(
                checkpoint.evolve(
                    processed_count=processed,
                    published_count=published,
                    failed_count=failed if failed > 0 else (1 if fail_status == "failed" else 0),
                    last_successful_event_key=last_key,
                    completed_slices=tuple(completed_list),
                    updated_at=completed_at,
                    completed=False,
                    terminal_status=None,
                )
            )
            self.audit_sink.record_run(
                BackfillRunAudit(
                    backfill_id=bid,
                    provider=request.provider,
                    source_kind=request.source_kind,
                    mode=mode,
                    request_fingerprint=fingerprint,
                    selector_summary=request.selector_summary(),
                    start_time=request.start_time,
                    end_time=request.end_time,
                    sink_type=sink_type,
                    slice_count=len(slices),
                    processed_count=processed,
                    published_count=published,
                    failed_count=failed,
                    started_at=started_at,
                    completed_at=completed_at,
                    terminal_status=fail_status,
                )
            )
            raise
        finally:
            if orchestrator is not None:
                await orchestrator.aclose()

    async def _prepare_checkpoint(
        self,
        *,
        request: BackfillRequest,
        backfill_id: str,
        fingerprint: str,
        started_at: datetime,
    ) -> BackfillCheckpoint:
        existing: BackfillCheckpoint | None = None
        if self.settings.checkpoint_enabled and self.checkpoint_store is not None:
            existing = await self.checkpoint_store.load(backfill_id)

        if existing is None:
            return BackfillCheckpoint(
                backfill_id=backfill_id,
                request_fingerprint=fingerprint,
                provider=request.provider,
                source_kind=request.source_kind,
                started_at=started_at,
                updated_at=started_at,
            )

        if existing.request_fingerprint != fingerprint:
            raise BackfillCheckpointMismatchError(detail="request fingerprint mismatch")
        if existing.provider != request.provider:
            raise BackfillCheckpointMismatchError(detail="provider mismatch")
        if existing.source_kind != request.source_kind:
            raise BackfillCheckpointMismatchError(detail="source_kind mismatch")
        if existing.completed:
            if not request.allow_completed_rerun:
                raise BackfillCompletedError(
                    detail="completed backfill requires allow_completed_rerun"
                )
            return BackfillCheckpoint(
                backfill_id=backfill_id,
                request_fingerprint=fingerprint,
                provider=request.provider,
                source_kind=request.source_kind,
                started_at=started_at,
                updated_at=started_at,
            )
        if (
            not request.resume
            and existing.current_slice is not None
            and request.checkpoint_id is None
        ):
            raise BackfillCheckpointMismatchError(
                detail="partial checkpoint exists; set resume=true or checkpoint_id"
            )
        return existing

    async def _persist(self, checkpoint: BackfillCheckpoint) -> None:
        if not self.settings.checkpoint_enabled or self.checkpoint_store is None:
            return
        await self.checkpoint_store.save(checkpoint)

    async def _handle_event(
        self,
        *,
        event: CanonicalMarketEvent,
        mode: BackfillMode,
        orchestrator: MarketDataOrchestrator,
        backfill_id: str,
    ) -> tuple[BackfillDecision, str, str | None]:
        if mode in {BackfillMode.DRY_RUN, BackfillMode.VALIDATE_ONLY}:
            ctx = initial_context(event, clock=self.clock, correlation_id=backfill_id)
            ctx = run_validation_stage(ctx, pipeline_id=orchestrator.pipeline_id)
            if ctx.decision is PipelineDecision.REJECTED_VALIDATION:
                return (
                    BackfillDecision.REJECTED_VALIDATION,
                    ctx.reason or "rejected_validation",
                    None,
                )
            ctx = run_pit_stage(ctx, pipeline_id=orchestrator.pipeline_id)
            if ctx.decision is PipelineDecision.REJECTED_PIT:
                return BackfillDecision.REJECTED_PIT, ctx.reason or "rejected_pit", None
            ctx = run_quality_stage(ctx)
            _ = run_routing_stage(ctx)
            if mode is BackfillMode.DRY_RUN:
                return BackfillDecision.DRY_RUN_VALIDATED, "dry_run", None
            return BackfillDecision.VALIDATED, "validated", None

        result = await orchestrator.process(event, correlation_id=backfill_id)
        if result.decision is PipelineDecision.PUBLISHED:
            return (
                BackfillDecision.PUBLISHED,
                "published",
                result.context.metadata.get("sink_message_id"),
            )
        if result.decision is PipelineDecision.REJECTED_VALIDATION:
            return (
                BackfillDecision.REJECTED_VALIDATION,
                result.context.reason or "rejected_validation",
                None,
            )
        if result.decision is PipelineDecision.REJECTED_PIT:
            return BackfillDecision.REJECTED_PIT, result.context.reason or "rejected_pit", None
        return (
            BackfillDecision.SINK_FAILED,
            result.context.reason or result.decision.value,
            result.context.metadata.get("sink_message_id"),
        )


def _resolve_sink_type(
    mode: BackfillMode,
    *,
    publish_port: PublishPort | None,
) -> BackfillSinkType:
    expected = sink_type_for_mode(mode)
    if mode is BackfillMode.PUBLISH:
        if publish_port is None:
            raise BackfillSinkRequiredError(detail="publish requires explicit PublishPort")
        return "publish_port"
    if publish_port is not None:
        raise BackfillInvalidRequestError(detail=f"{mode.value} must not receive a sink")
    _ = expected
    return "none"


def _order_events(
    events: list[CanonicalMarketEvent],
    *,
    slice_start: datetime,
) -> list[CanonicalMarketEvent]:
    return sorted(
        events,
        key=lambda e: (
            slice_start,
            e.occurred_at,
            e.event_type.value,
            e.instrument.instrument_key,
            build_idempotency_key(e),
        ),
    )


def build_backfill_engine(
    settings: BackfillSettings,
    *,
    clock: Clock,
    source_registry: BackfillSourceRegistry,
    checkpoint_store: BackfillCheckpointStore | None = None,
    audit_sink: BackfillAuditSink | None = None,
    sleeper: BackfillSleeper | None = None,
    owns_checkpoint: bool = True,
) -> BackfillEngine:
    if not settings.enabled:
        raise BackfillDisabledError(detail="cannot construct BackfillEngine while disabled")
    engine = BackfillEngine(
        settings=settings,
        clock=clock,
        source_registry=source_registry,
        checkpoint_store=checkpoint_store,
        audit_sink=audit_sink or InMemoryBackfillAuditSink(),
        sleeper=sleeper or AsyncioBackfillSleeper(),
    )
    engine._owns_checkpoint = owns_checkpoint
    return engine
