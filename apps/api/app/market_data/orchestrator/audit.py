"""Append-only pipeline audit records (#305).

Never store full payloads, provider bodies, or credentials.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.market_data.orchestrator.policies import PipelineDecision

# Terminal decisions that may appear in the audit sink.
TERMINAL_AUDIT_DECISIONS: frozenset[PipelineDecision] = frozenset(
    {
        PipelineDecision.PUBLISHED,
        PipelineDecision.DRY_RUN,
        PipelineDecision.DUPLICATE_SUPPRESSED,
        PipelineDecision.REJECTED_VALIDATION,
        PipelineDecision.REJECTED_PIT,
        PipelineDecision.BUFFER_OVERFLOW,
        PipelineDecision.PUBLISH_FAILED,
    }
)


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """One append-only terminal (or diagnostic) processing trail entry."""

    pipeline_id: str
    event_type: str
    instrument_key: str
    dedup_key: str | None
    idempotency_key: str | None
    routing_key: str | None
    correlation_id: str | None
    received_at: datetime
    completed_at: datetime
    decision: PipelineDecision
    reason_code: str
    error_type: str | None = None
    sink_message_id: str | None = None

    def __post_init__(self) -> None:
        if self.decision not in TERMINAL_AUDIT_DECISIONS:
            msg = f"audit decision must be terminal, got {self.decision!r}"
            raise ValueError(msg)


class AuditSink(Protocol):
    """Append-only audit destination."""

    def record(self, entry: AuditRecord) -> None: ...

    def records(self) -> Sequence[AuditRecord]: ...

    def clear(self) -> None: ...


class InMemoryAuditSink:
    """Bounded in-memory audit trail for application and tests."""

    def __init__(self, *, max_records: int = 10_000) -> None:
        if max_records < 1:
            msg = "max_records must be >= 1"
            raise ValueError(msg)
        self._max_records = max_records
        self._entries: list[AuditRecord] = []

    def record(self, entry: AuditRecord) -> None:
        if entry.decision not in TERMINAL_AUDIT_DECISIONS:
            msg = f"refusing non-terminal audit decision {entry.decision!r}"
            raise ValueError(msg)
        self._entries.append(entry)
        overflow = len(self._entries) - self._max_records
        if overflow > 0:
            del self._entries[0:overflow]

    def records(self) -> Sequence[AuditRecord]:
        return tuple(self._entries)

    def clear(self) -> None:
        self._entries.clear()
