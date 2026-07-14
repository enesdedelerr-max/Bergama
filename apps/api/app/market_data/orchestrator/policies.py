"""Immutable pipeline policy values and decision taxonomy (#305)."""

from __future__ import annotations

from enum import StrEnum


class PipelineDecision(StrEnum):
    """Processing outcomes for a single event.

    Intermediate:
    - PENDING — still progressing stages
    - ACCEPTED — admitted past early stages / into publish path (not delivered)

    Terminal:
    - PUBLISHED — only successful live delivery
    - DRY_RUN — observable dry-run, not delivered
    - DUPLICATE_SUPPRESSED
    - REJECTED_VALIDATION
    - REJECTED_PIT
    - BUFFER_OVERFLOW — admission capacity timeout
    - PUBLISH_FAILED
    """

    PENDING = "pending"
    ACCEPTED = "accepted"
    PUBLISHED = "published"
    DUPLICATE_SUPPRESSED = "duplicate_suppressed"
    REJECTED_VALIDATION = "rejected_validation"
    REJECTED_PIT = "rejected_pit"
    BUFFER_OVERFLOW = "buffer_overflow"
    PUBLISH_FAILED = "publish_failed"
    DRY_RUN = "dry_run"


TERMINAL_DECISIONS: frozenset[PipelineDecision] = frozenset(
    {
        PipelineDecision.PUBLISHED,
        PipelineDecision.DUPLICATE_SUPPRESSED,
        PipelineDecision.REJECTED_VALIDATION,
        PipelineDecision.REJECTED_PIT,
        PipelineDecision.BUFFER_OVERFLOW,
        PipelineDecision.PUBLISH_FAILED,
        PipelineDecision.DRY_RUN,
    }
)

SUCCESSFUL_DELIVERY_DECISIONS: frozenset[PipelineDecision] = frozenset({PipelineDecision.PUBLISHED})
