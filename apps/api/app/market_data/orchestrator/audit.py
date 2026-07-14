"""Append-only pipeline audit records (#305)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.market_data.orchestrator.policies import PipelineDecision


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """Minimum observable processing trail for one pipeline decision."""

    pipeline_id: str
    decision: PipelineDecision
    routing_key: str | None
    dedup_key: str | None
    idempotency_key: str | None
    received_at: datetime
    decided_at: datetime
    correlation_id: str | None
    reason: str


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
        self._entries.append(entry)
        overflow = len(self._entries) - self._max_records
        if overflow > 0:
            del self._entries[0:overflow]

    def records(self) -> Sequence[AuditRecord]:
        return tuple(self._entries)

    def clear(self) -> None:
        self._entries.clear()
