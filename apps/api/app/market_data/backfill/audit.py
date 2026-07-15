"""Backfill audit records (#309). Safe fields only."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.market_data.backfill.models import (
    BackfillDecision,
    BackfillMode,
    BackfillProvider,
    BackfillSinkType,
    BackfillSourceKind,
    BackfillTerminalStatus,
    SliceStatus,
)


@dataclass(frozen=True, slots=True)
class BackfillRunAudit:
    backfill_id: str
    provider: BackfillProvider
    source_kind: BackfillSourceKind
    mode: BackfillMode
    request_fingerprint: str
    selector_summary: dict[str, Any]
    start_time: datetime
    end_time: datetime
    sink_type: BackfillSinkType
    slice_count: int
    processed_count: int
    published_count: int
    failed_count: int
    started_at: datetime
    completed_at: datetime | None
    terminal_status: BackfillTerminalStatus | None


@dataclass(frozen=True, slots=True)
class BackfillSliceAudit:
    backfill_id: str
    slice_id: str
    start_time: datetime
    end_time: datetime
    provider_cursor_summary: dict[str, str]
    request_count: int
    event_count: int
    status: SliceStatus
    failure_reason: str | None = None


@dataclass(frozen=True, slots=True)
class BackfillEventAudit:
    backfill_id: str
    idempotency_key: str
    event_type: str
    instrument_key: str
    occurred_at: datetime
    decision: BackfillDecision
    reason: str
    processed_at: datetime
    sink_message_id: str | None = None


@dataclass(slots=True)
class InMemoryBackfillAuditSink:
    runs: list[BackfillRunAudit] = field(default_factory=list)
    slices: list[BackfillSliceAudit] = field(default_factory=list)
    events: list[BackfillEventAudit] = field(default_factory=list)

    def record_run(self, record: BackfillRunAudit) -> None:
        self.runs.append(record)

    def record_slice(self, record: BackfillSliceAudit) -> None:
        self.slices.append(record)

    def record_event(self, record: BackfillEventAudit) -> None:
        self.events.append(record)

    def clear(self) -> None:
        self.runs.clear()
        self.slices.clear()
        self.events.clear()
