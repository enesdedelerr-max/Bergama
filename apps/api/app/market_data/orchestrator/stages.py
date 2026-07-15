"""Single-responsibility pipeline stages (#305)."""

from __future__ import annotations

from datetime import datetime

from pydantic import ValidationError

from app.core.clock import Clock
from app.market_data.data_quality import DataQualityService, QualityAction
from app.market_data.envelope import CanonicalMarketEvent, parse_canonical_market_event
from app.market_data.keys import build_deduplication_key, build_idempotency_key
from app.market_data.orchestrator.audit import AuditRecord
from app.market_data.orchestrator.context import PipelineContext
from app.market_data.orchestrator.dedup import (
    BoundedDedupStore,
    DedupReserveOutcome,
    DedupReserveResult,
)
from app.market_data.orchestrator.policies import PipelineDecision
from app.market_data.orchestrator.routing import routing_key_for
from app.market_data.orchestrator.sequencing import StreamSequenceInfo
from app.market_data.timing import validate_point_in_time_order


def build_terminal_audit(
    context: PipelineContext,
    *,
    pipeline_id: str,
    decision: PipelineDecision,
    reason_code: str,
    completed_at: datetime,
    error_type: str | None = None,
    sink_message_id: str | None = None,
) -> AuditRecord:
    """Build a single terminal audit record (no payloads / secrets)."""
    event = context.event
    return AuditRecord(
        pipeline_id=pipeline_id,
        event_type=event.event_type.value,
        instrument_key=event.instrument.instrument_key,
        dedup_key=context.dedup_key,
        idempotency_key=context.idempotency_key,
        routing_key=context.routing_key,
        correlation_id=context.correlation_id,
        received_at=context.received_at,
        completed_at=completed_at,
        decision=decision,
        reason_code=reason_code,
        error_type=error_type,
        sink_message_id=sink_message_id,
        quality_assessment_id=(
            context.quality_assessment.assessment_id
            if context.quality_assessment is not None
            else None
        ),
        quality_status=(
            context.quality_assessment.overall_status.value
            if context.quality_assessment is not None
            else None
        ),
        quality_highest_severity=(
            context.quality_assessment.highest_severity.value
            if context.quality_assessment is not None
            else None
        ),
        quality_action=(
            context.quality_assessment.recommended_action.value
            if context.quality_assessment is not None
            else None
        ),
    )


def run_validation_stage(context: PipelineContext, *, pipeline_id: str) -> PipelineContext:
    """Re-validate canonical schema/decimals/types. Never weaken model rules.

    Canonical Pydantic construction rejects invalid PIT orderings. Those failures
    surface here as ``REJECTED_VALIDATION`` because the event never formed a
    valid canonical instance for the PIT stage. See sprint docs.
    """
    _ = pipeline_id
    if context.decision is not PipelineDecision.PENDING:
        return context
    try:
        payload = context.event.model_dump(mode="python")
        parsed = parse_canonical_market_event(payload)
    except (ValidationError, ValueError, TypeError) as exc:
        decision = PipelineDecision.REJECTED_VALIDATION
        return context.evolve(
            decision=decision,
            reason="rejected_validation",
            metadata={
                **dict(context.metadata),
                "error_type": type(exc).__name__,
                "error_detail": str(exc)[:256],
            },
        )
    return context.evolve(event=parsed, quality=parsed.quality)


def run_pit_stage(context: PipelineContext, *, pipeline_id: str) -> PipelineContext:
    """Recheck point-in-time policy for a valid canonical event. Never repairs.

    ``REJECTED_PIT`` is only used when this stage fails. Invalid PIT orderings
    that cannot survive canonical model construction are rejected earlier as
    validation failures.
    """
    _ = pipeline_id
    if context.decision is not PipelineDecision.PENDING:
        return context
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
        return context.evolve(
            decision=PipelineDecision.REJECTED_PIT,
            reason="rejected_pit",
            metadata={
                **dict(context.metadata),
                "error_type": type(exc).__name__,
                "error_detail": str(exc)[:256],
            },
        )
    return context


def run_quality_stage(
    context: PipelineContext,
    *,
    service: DataQualityService | None = None,
) -> PipelineContext:
    """Preserve connector quality flags; never invent provider-specific flags."""
    if context.decision is not PipelineDecision.PENDING:
        return context
    if service is None:
        return context.evolve(quality=context.event.quality)

    assessment = service.evaluate(context.event)
    metadata = {
        **dict(context.metadata),
        "quality_assessment_id": assessment.assessment_id,
        "quality_status": assessment.overall_status.value,
        "quality_highest_severity": assessment.highest_severity.value,
        "quality_action": assessment.recommended_action.value,
    }
    enriched = context.evolve(
        quality=context.event.quality,
        quality_assessment=assessment,
        metadata=metadata,
    )
    if assessment.recommended_action is QualityAction.REJECT:
        return enriched.evolve(
            decision=PipelineDecision.QUALITY_REJECTED,
            reason="quality_rejected",
        )
    if assessment.recommended_action is QualityAction.HALT_PIPELINE:
        return enriched.evolve(
            decision=PipelineDecision.QUALITY_HALT,
            reason="quality_halt",
            metadata={**metadata, "error_type": "DataQualityHaltError"},
        )
    return enriched


async def run_dedup_stage(
    context: PipelineContext,
    *,
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
        return enriched.evolve(
            decision=PipelineDecision.DUPLICATE_SUPPRESSED,
            reason="duplicate_suppressed",
        ), result
    if result.outcome is DedupReserveOutcome.CAPACITY_EXHAUSTED:
        return enriched.evolve(
            decision=PipelineDecision.BUFFER_OVERFLOW,
            reason="dedup_store_capacity_exhausted",
        ), result
    return enriched, result


def apply_sequence(
    context: PipelineContext,
    *,
    info: StreamSequenceInfo,
) -> PipelineContext:
    """Annotate per-stream sequence without reordering timestamps."""
    if context.decision is not PipelineDecision.PENDING:
        return context
    return context.evolve(
        order_scope=info.stream_key,
        order_sequence=info.sequence,
        out_of_order=info.out_of_order,
        metadata={
            **dict(context.metadata),
            "stream_key": info.stream_key,
            "order_sequence": str(info.sequence),
            "out_of_order": "true" if info.out_of_order else "false",
        },
    )


def run_routing_stage(context: PipelineContext) -> PipelineContext:
    """Attach canonical routing_key only."""
    if context.decision is not PipelineDecision.PENDING:
        return context
    return context.evolve(routing_key=routing_key_for(context.event))


def mark_accepted(context: PipelineContext, *, reason: str = "admitted") -> PipelineContext:
    """Intermediate admission marker — never a terminal audit decision."""
    return context.evolve(decision=PipelineDecision.ACCEPTED, reason=reason)


def finalize_decision(
    context: PipelineContext,
    *,
    decision: PipelineDecision,
    reason_code: str,
    error_type: str | None = None,
    sink_message_id: str | None = None,
) -> PipelineContext:
    return context.evolve(
        decision=decision,
        reason=reason_code,
        metadata={
            **dict(context.metadata),
            **({"error_type": error_type} if error_type else {}),
            **({"sink_message_id": sink_message_id} if sink_message_id else {}),
        },
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
