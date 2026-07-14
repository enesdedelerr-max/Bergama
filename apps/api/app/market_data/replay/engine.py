"""Deterministic Replay Engine (#308).

Flow:
  ReplayRequest → IcebergReplaySource → reconstruct → order →
  isolated MarketDataOrchestrator → explicit sink or none → audit → checkpoint

Never calls provider SDKs. Never mutates Kafka offsets. Never auto-selects
production KafkaPublishAdapter. Sequential MVP processing for deterministic
checkpointing. At-least-once republish only — no exactly-once claim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.core.clock import Clock
from app.core.logging import get_logger, structured_extra
from app.core.orchestrator_settings import OrchestratorSettings
from app.core.replay_settings import ReplaySettings
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
from app.market_data.replay.audit import (
    InMemoryReplayAuditSink,
    ReplayEventAudit,
    ReplayRunAudit,
)
from app.market_data.replay.checkpoint import ReplayCheckpoint
from app.market_data.replay.errors import (
    ReplayCancelledError,
    ReplayCheckpointMismatchError,
    ReplayClosedError,
    ReplayCompletedError,
    ReplayDisabledError,
    ReplayError,
    ReplayIdempotencyMismatchError,
    ReplayInvalidRequestError,
    ReplayPitError,
    ReplaySinkFailedError,
    ReplaySinkRequiredError,
    ReplayValidationError,
)
from app.market_data.replay.models import (
    ReplayDecision,
    ReplayMode,
    ReplayRecord,
    ReplayRequest,
    ReplayRunResult,
    ReplaySinkType,
    ReplayTerminalStatus,
    new_replay_id,
)
from app.market_data.replay.ordering import filter_after_cursor, sort_replay_records
from app.market_data.replay.policies import (
    AsyncioReplaySleeper,
    TokenBucketRateLimiter,
    resolve_limits,
    sink_type_for_mode,
)
from app.market_data.replay.ports import (
    CheckpointStore,
    ReplayAuditSink,
    ReplayCustomSink,
    ReplaySleeper,
    ReplaySource,
)

logger = get_logger(__name__)


@dataclass(slots=True)
class ReplayEngine:
    """Application-scoped replay runner. Explicit ``run()`` only — no startup jobs."""

    settings: ReplaySettings
    clock: Clock
    source: ReplaySource
    checkpoint_store: CheckpointStore | None = None
    audit_sink: ReplayAuditSink = field(default_factory=InMemoryReplayAuditSink)
    sleeper: ReplaySleeper = field(default_factory=AsyncioReplaySleeper)
    _closed: bool = field(default=False, init=False, repr=False)
    _cancel_requested: bool = field(default=False, init=False, repr=False)
    _owns_source: bool = field(default=True, repr=False)
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
        if self._owns_source:
            await self.source.aclose()
        if self._owns_checkpoint and self.checkpoint_store is not None:
            await self.checkpoint_store.aclose()
        self.audit_sink.clear()

    async def run(
        self,
        request: ReplayRequest,
        *,
        replay_id: str | None = None,
        publish_port: PublishPort | None = None,
        custom_sink: ReplayCustomSink | None = None,
    ) -> ReplayRunResult:
        if self._closed:
            raise ReplayClosedError()
        if not self.settings.enabled:
            raise ReplayDisabledError(detail="replay engine is disabled")

        self._cancel_requested = False
        mode = request.mode
        sink_type = _resolve_sink_type(mode, publish_port=publish_port, custom_sink=custom_sink)
        limits = resolve_limits(request, self.settings)
        rid = (replay_id or request.checkpoint_id or new_replay_id()).strip()
        if not rid:
            raise ReplayInvalidRequestError(detail="replay_id must be non-empty")
        fingerprint = request.fingerprint(sink_type=sink_type)
        started_at = self.clock.now()

        checkpoint = await self._prepare_checkpoint(
            request=request,
            replay_id=rid,
            fingerprint=fingerprint,
            mode=mode,
            started_at=started_at,
        )

        filters = {
            "start_time": request.start_time.isoformat(),
            "end_time": request.end_time.isoformat(),
            "event_types": list(request.event_types),
            "instrument_keys": list(request.instrument_keys),
            "source_providers": list(request.source_providers),
            "max_records": request.max_records,
            "batch_size": limits.batch_size,
        }
        self.audit_sink.record_run(
            ReplayRunAudit(
                replay_id=rid,
                mode=mode,
                request_fingerprint=fingerprint,
                source="iceberg",
                sink_type=sink_type,
                filters=filters,
                started_at=started_at,
                completed_at=None,
                processed_count=checkpoint.processed_count,
                succeeded_count=checkpoint.succeeded_count,
                failed_count=checkpoint.failed_count,
                last_cursor=checkpoint.last_cursor,
                terminal_status=None,
            )
        )

        orchestrator: MarketDataOrchestrator | None = None
        processed = checkpoint.processed_count
        succeeded = checkpoint.succeeded_count
        failed = checkpoint.failed_count
        last_cursor = checkpoint.last_cursor
        synthetic_count = 0
        terminal: ReplayTerminalStatus = "failed"

        try:
            records = await self.source.fetch(request)
            ordered = sort_replay_records(records)
            pending = filter_after_cursor(ordered, checkpoint.last_cursor)
            # Harden max_records after resume (source may have returned the global cap).
            pending = pending[: request.max_records]

            rate = TokenBucketRateLimiter(
                events_per_second=limits.events_per_second,
                sleeper=self.sleeper,
            )

            if mode in {ReplayMode.REPUBLISH, ReplayMode.CUSTOM_SINK}:
                sink: PublishPort | ReplayCustomSink
                if mode is ReplayMode.REPUBLISH:
                    assert publish_port is not None
                    sink = publish_port
                else:
                    assert custom_sink is not None
                    sink = custom_sink
                orch_settings = OrchestratorSettings(
                    enabled=True,
                    dry_run=False,
                    publish_backend="none",
                    pipeline_name=f"replay-{rid[:8]}",
                    max_in_flight=limits.max_in_flight,
                    admission_timeout_seconds=0.05,
                )
                orchestrator = build_market_data_orchestrator(
                    orch_settings,
                    clock=self.clock,
                    publish_port=sink,
                )
            else:
                # Isolated orchestrator for non-publish modes (fresh dedup/state).
                orch_settings = OrchestratorSettings(
                    enabled=True,
                    dry_run=True,
                    publish_backend="none",
                    pipeline_name=f"replay-{rid[:8]}",
                    max_in_flight=limits.max_in_flight,
                    admission_timeout_seconds=0.05,
                )
                orchestrator = build_market_data_orchestrator(
                    orch_settings,
                    clock=self.clock,
                )

            for record in pending:
                if self._cancel_requested:
                    raise ReplayCancelledError(detail="cancel requested")
                await rate.admit(cancelled=self._cancel_requested)

                event, decision, reason, sink_msg, synth = await self._handle_record(
                    record=record,
                    mode=mode,
                    orchestrator=orchestrator,
                    replay_id=rid,
                )
                _ = event
                processed += 1
                if synth:
                    synthetic_count += 1

                self.audit_sink.record_event(
                    ReplayEventAudit(
                        replay_id=rid,
                        idempotency_key=record.idempotency_key,
                        event_type=record.event_type,
                        instrument_key=record.instrument_key,
                        replay_cursor=record.cursor(),
                        decision=decision,
                        reason_code=reason,
                        replay_processed_at=self.clock.now(),
                        sink_message_id=sink_msg,
                        synthetic_symbol_effective_from=synth
                        or record.synthetic_symbol_effective_from,
                    )
                )

                if decision in {
                    ReplayDecision.REJECTED_VALIDATION,
                    ReplayDecision.REJECTED_PIT,
                    ReplayDecision.SINK_FAILED,
                }:
                    failed += 1
                    await self._persist_checkpoint(
                        ReplayCheckpoint(
                            replay_id=rid,
                            request_fingerprint=fingerprint,
                            mode=mode,
                            source="iceberg",
                            last_cursor=last_cursor,
                            processed_count=processed,
                            succeeded_count=succeeded,
                            failed_count=failed,
                            started_at=checkpoint.started_at,
                            updated_at=self.clock.now(),
                            completed=False,
                            terminal_status=None,
                        )
                    )
                    if decision is ReplayDecision.REJECTED_VALIDATION:
                        raise ReplayValidationError(detail=reason)
                    if decision is ReplayDecision.REJECTED_PIT:
                        raise ReplayPitError(detail=reason)
                    raise ReplaySinkFailedError(detail=reason)

                succeeded += 1
                last_cursor = record.cursor()
                await self._persist_checkpoint(
                    ReplayCheckpoint(
                        replay_id=rid,
                        request_fingerprint=fingerprint,
                        mode=mode,
                        source="iceberg",
                        last_cursor=last_cursor,
                        processed_count=processed,
                        succeeded_count=succeeded,
                        failed_count=failed,
                        started_at=checkpoint.started_at,
                        updated_at=self.clock.now(),
                        completed=False,
                        terminal_status=None,
                    )
                )

            terminal = "completed_empty" if succeeded == 0 and failed == 0 else "completed"
            completed_at = self.clock.now()
            final = ReplayCheckpoint(
                replay_id=rid,
                request_fingerprint=fingerprint,
                mode=mode,
                source="iceberg",
                last_cursor=last_cursor,
                processed_count=processed,
                succeeded_count=succeeded,
                failed_count=failed,
                started_at=checkpoint.started_at,
                updated_at=completed_at,
                completed_at=completed_at,
                completed=True,
                terminal_status=terminal,
            )
            await self._persist_checkpoint(final)
            result = ReplayRunResult(
                replay_id=rid,
                mode=mode,
                request_fingerprint=fingerprint,
                source="iceberg",
                sink_type=sink_type,
                started_at=started_at,
                completed_at=completed_at,
                processed_count=processed,
                succeeded_count=succeeded,
                failed_count=failed,
                last_cursor=last_cursor,
                terminal_status=terminal,
                synthetic_reconstruction_count=synthetic_count,
            )
            self.audit_sink.record_run(
                ReplayRunAudit(
                    replay_id=rid,
                    mode=mode,
                    request_fingerprint=fingerprint,
                    source="iceberg",
                    sink_type=sink_type,
                    filters=filters,
                    started_at=started_at,
                    completed_at=completed_at,
                    processed_count=processed,
                    succeeded_count=succeeded,
                    failed_count=failed,
                    last_cursor=last_cursor,
                    terminal_status=terminal,
                )
            )
            logger.info(
                "replay run completed",
                extra=structured_extra(
                    event="market_data.replay.completed",
                    source="market_data.replay",
                    replay_id=rid,
                    mode=mode.value,
                    processed_count=processed,
                    succeeded_count=succeeded,
                    failed_count=failed,
                    terminal_status=terminal,
                ),
            )
            return result
        except ReplayError as exc:
            completed_at = self.clock.now()
            status: ReplayTerminalStatus = (
                "cancelled" if isinstance(exc, ReplayCancelledError) else "failed"
            )
            await self._persist_checkpoint(
                ReplayCheckpoint(
                    replay_id=rid,
                    request_fingerprint=fingerprint,
                    mode=mode,
                    source="iceberg",
                    last_cursor=last_cursor,
                    processed_count=processed,
                    succeeded_count=succeeded,
                    failed_count=failed if failed > 0 else (1 if status == "failed" else 0),
                    started_at=checkpoint.started_at,
                    updated_at=completed_at,
                    completed_at=None,
                    completed=False,
                    terminal_status=None,
                )
            )
            self.audit_sink.record_run(
                ReplayRunAudit(
                    replay_id=rid,
                    mode=mode,
                    request_fingerprint=fingerprint,
                    source="iceberg",
                    sink_type=sink_type,
                    filters=filters,
                    started_at=started_at,
                    completed_at=completed_at,
                    processed_count=processed,
                    succeeded_count=succeeded,
                    failed_count=failed,
                    last_cursor=last_cursor,
                    terminal_status=status,
                )
            )
            raise
        finally:
            if orchestrator is not None:
                await orchestrator.aclose()

    async def _prepare_checkpoint(
        self,
        *,
        request: ReplayRequest,
        replay_id: str,
        fingerprint: str,
        mode: ReplayMode,
        started_at: datetime,
    ) -> ReplayCheckpoint:
        existing: ReplayCheckpoint | None = None
        if self.settings.checkpoint_enabled and self.checkpoint_store is not None:
            existing = await self.checkpoint_store.load(replay_id)

        if existing is None:
            return ReplayCheckpoint(
                replay_id=replay_id,
                request_fingerprint=fingerprint,
                mode=mode,
                source="iceberg",
                last_cursor=None,
                processed_count=0,
                succeeded_count=0,
                failed_count=0,
                started_at=started_at,
                updated_at=started_at,
                completed=False,
                terminal_status=None,
            )

        if existing.request_fingerprint != fingerprint:
            raise ReplayCheckpointMismatchError(detail="request fingerprint mismatch")
        if existing.mode != mode:
            raise ReplayCheckpointMismatchError(detail="mode mismatch")
        if existing.source != "iceberg":
            raise ReplayCheckpointMismatchError(detail="source mismatch")
        if existing.completed:
            if not request.allow_completed_rerun:
                raise ReplayCompletedError(detail="completed replay requires allow_completed_rerun")
            # Explicit rerun: reset cursor progress while keeping identity.
            return ReplayCheckpoint(
                replay_id=replay_id,
                request_fingerprint=fingerprint,
                mode=mode,
                source="iceberg",
                last_cursor=None,
                processed_count=0,
                succeeded_count=0,
                failed_count=0,
                started_at=started_at,
                updated_at=started_at,
                completed=False,
                terminal_status=None,
            )
        # Resuming without resume=true is allowed when checkpoint_id was supplied;
        # otherwise require explicit resume for partial checkpoints.
        if (
            not request.resume
            and existing.last_cursor is not None
            and request.checkpoint_id is None
        ):
            raise ReplayCheckpointMismatchError(
                detail="partial checkpoint exists; set resume=true or checkpoint_id"
            )
        return existing

    async def _persist_checkpoint(self, checkpoint: ReplayCheckpoint) -> None:
        if not self.settings.checkpoint_enabled or self.checkpoint_store is None:
            return
        await self.checkpoint_store.save(checkpoint)

    async def _handle_record(
        self,
        *,
        record: ReplayRecord,
        mode: ReplayMode,
        orchestrator: MarketDataOrchestrator,
        replay_id: str,
    ) -> tuple[CanonicalMarketEvent, ReplayDecision, str, str | None, bool]:
        event = record.event
        synthetic = record.synthetic_symbol_effective_from
        recomputed = build_idempotency_key(event)
        if recomputed != record.idempotency_key:
            raise ReplayIdempotencyMismatchError(detail="stored idempotency_key mismatch")

        if mode in {ReplayMode.DRY_RUN, ReplayMode.VALIDATE_ONLY}:
            ctx = initial_context(event, clock=self.clock, correlation_id=replay_id)
            ctx = run_validation_stage(ctx, pipeline_id=orchestrator.pipeline_id)
            if ctx.decision is PipelineDecision.REJECTED_VALIDATION:
                return (
                    event,
                    ReplayDecision.REJECTED_VALIDATION,
                    ctx.reason or "rejected_validation",
                    None,
                    synthetic,
                )
            ctx = run_pit_stage(ctx, pipeline_id=orchestrator.pipeline_id)
            if ctx.decision is PipelineDecision.REJECTED_PIT:
                return (
                    event,
                    ReplayDecision.REJECTED_PIT,
                    ctx.reason or "rejected_pit",
                    None,
                    synthetic,
                )
            ctx = run_quality_stage(ctx)
            _ = run_routing_stage(ctx)
            if mode is ReplayMode.DRY_RUN:
                return event, ReplayDecision.DRY_RUN_VALIDATED, "dry_run", None, synthetic
            return event, ReplayDecision.VALIDATED, "validated", None, synthetic

        # Republish / custom_sink via isolated orchestrator — preserves idempotency_key.
        result = await orchestrator.process(event, correlation_id=replay_id)
        if result.decision is PipelineDecision.PUBLISHED:
            decision = (
                ReplayDecision.REPUBLISHED
                if mode is ReplayMode.REPUBLISH
                else ReplayDecision.CUSTOM_SINK_SUCCEEDED
            )
            sink_id = result.context.metadata.get("sink_message_id")
            return event, decision, "published", sink_id, synthetic
        if result.decision is PipelineDecision.REJECTED_VALIDATION:
            return (
                event,
                ReplayDecision.REJECTED_VALIDATION,
                result.context.reason or "rejected_validation",
                None,
                synthetic,
            )
        if result.decision is PipelineDecision.REJECTED_PIT:
            return (
                event,
                ReplayDecision.REJECTED_PIT,
                result.context.reason or "rejected_pit",
                None,
                synthetic,
            )
        return (
            event,
            ReplayDecision.SINK_FAILED,
            result.context.reason or result.decision.value,
            result.context.metadata.get("sink_message_id"),
            synthetic,
        )


def _resolve_sink_type(
    mode: ReplayMode,
    *,
    publish_port: PublishPort | None,
    custom_sink: ReplayCustomSink | None,
) -> ReplaySinkType:
    expected = sink_type_for_mode(mode)
    if mode is ReplayMode.REPUBLISH:
        if publish_port is None:
            raise ReplaySinkRequiredError(detail="republish requires explicit PublishPort")
        if custom_sink is not None:
            raise ReplayInvalidRequestError(detail="republish cannot combine custom_sink")
        return "publish_port"
    if mode is ReplayMode.CUSTOM_SINK:
        if custom_sink is None:
            raise ReplaySinkRequiredError(detail="custom_sink mode requires explicit typed sink")
        if publish_port is not None:
            raise ReplayInvalidRequestError(detail="custom_sink cannot combine publish_port")
        return "custom_sink"
    if publish_port is not None or custom_sink is not None:
        raise ReplayInvalidRequestError(detail=f"{mode.value} must not receive a sink")
    _ = expected
    return "none"


def build_replay_engine(
    settings: ReplaySettings,
    *,
    clock: Clock,
    source: ReplaySource,
    checkpoint_store: CheckpointStore | None = None,
    audit_sink: ReplayAuditSink | None = None,
    sleeper: ReplaySleeper | None = None,
    owns_source: bool = True,
    owns_checkpoint: bool = True,
) -> ReplayEngine:
    """Construct a ReplayEngine. Does not start a replay."""
    if not settings.enabled:
        raise ReplayDisabledError(detail="cannot construct ReplayEngine while disabled")
    engine = ReplayEngine(
        settings=settings,
        clock=clock,
        source=source,
        checkpoint_store=checkpoint_store,
        audit_sink=audit_sink or InMemoryReplayAuditSink(),
        sleeper=sleeper or AsyncioReplaySleeper(),
    )
    engine._owns_source = owns_source
    engine._owns_checkpoint = owns_checkpoint
    return engine
