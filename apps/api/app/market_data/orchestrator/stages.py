"""Single-responsibility pipeline stages (#305)."""

from __future__ import annotations

from datetime import datetime

from pydantic import ValidationError

from app.core.clock import Clock
from app.market_data.envelope import CanonicalMarketEvent, parse_canonical_market_event
from app.market_data.keys import build_deduplication_key, build_idempotency_key
from app.market_data.orchestrator.audit import AuditRecord
from app.market_data.orchestrator.context import PipelineContext
from app.market_data.orchestrator.dedup import (
    BoundedDedupStore,
    DedupReserveOutcome,
    DedupReserveResult,
)
from app.market_data.orchestrator.ordering import OrderingTracker
from app.market_data.orchestrator.policies import PipelineDecision
from app.market_data.orchestrator.routing import routing_key_for
from app.market_data.timing import validate_point_in_time_order


def _audit(
    context: PipelineContext,
    *,
    pipeline_id: str,
    decision: PipelineDecision,
    reason: str,
    decided_at: datetime,
) -> AuditRecord:
    return AuditRecord(
        pipeline_id=pipeline_id,
        decision=decision,
        routing_key=context.routing_key,
        dedup_key=context.dedup_key,
        idempotency_key=context.idempotency_key,
        received_at=context.received_at,
        decided_at=decided_at,
        correlation_id=context.correlation_id,
        reason=reason,
    )


_PIT_ERROR_MARKERS = (
    "occurred_at must be",
    "known_at must be",
    "revisions require",
    "revision_of_event_id requires",
)


def _looks_like_pit_failure(exc: BaseException) -> bool:
    texts = [str(exc).lower()]
    if isinstance(exc, ValidationError):
        texts.extend(err.get("msg", "").lower() for err in exc.errors())
    return any(any(marker in text for marker in _PIT_ERROR_MARKERS) for text in texts if text)


def run_validation_stage(context: PipelineContext, *, pipeline_id: str) -> PipelineContext:
    """Re-validate canonical schema/decimals; defer PIT violations to PIT stage."""
    decided_at = context.pipeline_clock.now()
    try:
        payload = context.event.model_dump(mode="python")
        parsed = parse_canonical_market_event(payload)
    except (ValidationError, ValueError, TypeError) as exc:
        causes: list[BaseException] = [exc]
        if exc.__cause__ is not None:
            causes.append(exc.__cause__)
        if any(_looks_like_pit_failure(item) for item in causes):
            # Keep PENDING so PITStage owns the decision taxonomy.
            return context
        decision = PipelineDecision.REJECTED_VALIDATION
        record = _audit(
            context,
            pipeline_id=pipeline_id,
            decision=decision,
            reason=f"validation failed: {exc}",
            decided_at=decided_at,
        )
        return context.evolve(
            decision=decision,
            reason=str(exc),
            audit=(*context.audit, record),
        )
    return context.evolve(event=parsed, quality=parsed.quality)


def run_pit_stage(context: PipelineContext, *, pipeline_id: str) -> PipelineContext:
    """Re-run PIT ordering checks without repairing timestamps."""
    if context.decision is not PipelineDecision.PENDING:
        return context
    decided_at = context.pipeline_clock.now()
    event = context.event
    try:
        validate_point_in_time_order(
            occurred_at=event.occurred_at,
            effective_at=event.effective_at,
            known_at=event.known_at,
            ingested_at=event.ingested_at,
            quality=event.quality,
        )
    except ValueError as exc:
        decision = PipelineDecision.REJECTED_PIT
        record = _audit(
            context,
            pipeline_id=pipeline_id,
            decision=decision,
            reason=f"pit validation failed: {exc}",
            decided_at=decided_at,
        )
        return context.evolve(
            decision=decision,
            reason=str(exc),
            audit=(*context.audit, record),
        )
    return context


def run_quality_stage(context: PipelineContext) -> PipelineContext:
    """Preserve connector quality flags; never invent provider-specific flags."""
    if context.decision is not PipelineDecision.PENDING:
        return context
    return context.evolve(quality=context.event.quality)


async def run_dedup_stage(
    context: PipelineContext,
    *,
    pipeline_id: str,
    store: BoundedDedupStore,
) -> tuple[PipelineContext, DedupReserveResult | None]:
    """Reserve dedup key (do not commit). Revisions skip reservation."""
    if context.decision is not PipelineDecision.PENDING:
        return context, None

    decided_at = context.pipeline_clock.now()
    dedup_key = build_deduplication_key(context.event)
    idempotency_key = build_idempotency_key(context.event)
    enriched = context.evolve(dedup_key=dedup_key, idempotency_key=idempotency_key)

    result = await store.try_reserve(
        dedup_key,
        now=decided_at,
        is_revision=context.event.quality.is_revision,
    )
    if result.outcome is DedupReserveOutcome.SKIPPED_REVISION:
        return enriched.evolve(
            metadata={**dict(enriched.metadata), "dedup_revision_skip": "true"},
        ), result
    if result.outcome is DedupReserveOutcome.DUPLICATE:
        decision = PipelineDecision.DUPLICATE_SUPPRESSED
        record = _audit(
            enriched,
            pipeline_id=pipeline_id,
            decision=decision,
            reason=(
                "duplicate dedup_key already "
                f"{result.existing_state.value if result.existing_state else 'present'}"
            ),
            decided_at=decided_at,
        )
        return enriched.evolve(
            decision=decision,
            reason="duplicate_suppressed",
            audit=(*enriched.audit, record),
        ), result
    if result.outcome is DedupReserveOutcome.CAPACITY_EXHAUSTED:
        decision = PipelineDecision.BUFFER_OVERFLOW
        record = _audit(
            enriched,
            pipeline_id=pipeline_id,
            decision=decision,
            reason="dedup_store_capacity_exhausted",
            decided_at=decided_at,
        )
        return enriched.evolve(
            decision=decision,
            reason="dedup_store_capacity_exhausted",
            audit=(*enriched.audit, record),
        ), result
    return enriched, result


def run_ordering_stage(
    context: PipelineContext,
    *,
    tracker: OrderingTracker,
) -> PipelineContext:
    """Annotate per-(instrument, event_type) sequence without reordering."""
    if context.decision is not PipelineDecision.PENDING:
        return context
    decision = tracker.observe(context.event)
    return context.evolve(
        order_scope=decision.scope,
        order_sequence=decision.sequence,
        out_of_order=decision.out_of_order,
        metadata={
            **dict(context.metadata),
            "order_scope": decision.scope,
            "order_sequence": str(decision.sequence),
            "out_of_order": "true" if decision.out_of_order else "false",
        },
    )


def run_routing_stage(context: PipelineContext) -> PipelineContext:
    """Attach canonical routing_key only."""
    if context.decision is not PipelineDecision.PENDING:
        return context
    return context.evolve(routing_key=routing_key_for(context.event))


def mark_accepted(
    context: PipelineContext,
    *,
    pipeline_id: str,
    reason: str = "admitted",
) -> PipelineContext:
    """Intermediate admission — not a successful delivery outcome."""
    decided_at = context.pipeline_clock.now()
    decision = PipelineDecision.ACCEPTED
    record = _audit(
        context,
        pipeline_id=pipeline_id,
        decision=decision,
        reason=reason,
        decided_at=decided_at,
    )
    return context.evolve(
        decision=decision,
        reason=reason,
        audit=(*context.audit, record),
    )


def finalize_published(
    context: PipelineContext,
    *,
    pipeline_id: str,
    reason: str = "published",
) -> PipelineContext:
    decided_at = context.pipeline_clock.now()
    decision = PipelineDecision.PUBLISHED
    record = _audit(
        context,
        pipeline_id=pipeline_id,
        decision=decision,
        reason=reason,
        decided_at=decided_at,
    )
    return context.evolve(
        decision=decision,
        reason=reason,
        audit=(*context.audit, record),
    )


def finalize_buffer_overflow(
    context: PipelineContext, *, pipeline_id: str, detail: str
) -> PipelineContext:
    decided_at = context.pipeline_clock.now()
    decision = PipelineDecision.BUFFER_OVERFLOW
    record = _audit(
        context,
        pipeline_id=pipeline_id,
        decision=decision,
        reason=detail,
        decided_at=decided_at,
    )
    return context.evolve(
        decision=decision,
        reason=detail,
        audit=(*context.audit, record),
    )


def finalize_publish_failed(
    context: PipelineContext, *, pipeline_id: str, detail: str
) -> PipelineContext:
    decided_at = context.pipeline_clock.now()
    decision = PipelineDecision.PUBLISH_FAILED
    record = _audit(
        context,
        pipeline_id=pipeline_id,
        decision=decision,
        reason=detail,
        decided_at=decided_at,
    )
    return context.evolve(
        decision=decision,
        reason=detail,
        audit=(*context.audit, record),
    )


def finalize_dry_run(
    context: PipelineContext,
    *,
    pipeline_id: str,
    detail: str = "dry_run",
) -> PipelineContext:
    """Observable dry-run terminal state — never counted as a live publish."""
    decided_at = context.pipeline_clock.now()
    decision = PipelineDecision.DRY_RUN
    record = _audit(
        context,
        pipeline_id=pipeline_id,
        decision=decision,
        reason=detail,
        decided_at=decided_at,
    )
    return context.evolve(
        decision=decision,
        reason=detail,
        audit=(*context.audit, record),
    )


def initial_context(
    event: CanonicalMarketEvent,
    *,
    clock: Clock,
    correlation_id: str | None,
) -> PipelineContext:
    received_at = clock.now()
    return PipelineContext(
        event=event,
        dedup_key=None,
        idempotency_key=None,
        routing_key=None,
        decision=PipelineDecision.PENDING,
        quality=event.quality,
        received_at=received_at,
        pipeline_clock=clock,
        correlation_id=correlation_id,
        audit=(),
        metadata={},
    )
