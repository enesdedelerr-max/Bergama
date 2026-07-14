"""Replay-specific audit records (#308). Safe fields only — no payloads/secrets."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.market_data.replay.models import (
    ReplayCursor,
    ReplayDecision,
    ReplayMode,
    ReplaySinkType,
    ReplaySourceType,
    ReplayTerminalStatus,
)


@dataclass(frozen=True, slots=True)
class ReplayRunAudit:
    replay_id: str
    mode: ReplayMode
    request_fingerprint: str
    source: ReplaySourceType
    sink_type: ReplaySinkType
    filters: dict[str, Any]
    started_at: datetime
    completed_at: datetime | None
    processed_count: int
    succeeded_count: int
    failed_count: int
    last_cursor: ReplayCursor | None
    terminal_status: ReplayTerminalStatus | None


@dataclass(frozen=True, slots=True)
class ReplayEventAudit:
    replay_id: str
    idempotency_key: str
    event_type: str
    instrument_key: str
    replay_cursor: ReplayCursor
    decision: ReplayDecision
    reason_code: str
    replay_processed_at: datetime
    sink_message_id: str | None = None
    synthetic_symbol_effective_from: bool = False


@dataclass(slots=True)
class InMemoryReplayAuditSink:
    """Process-local audit sink for tests and offline runs."""

    runs: list[ReplayRunAudit] = field(default_factory=list)
    events: list[ReplayEventAudit] = field(default_factory=list)

    def record_run(self, record: ReplayRunAudit) -> None:
        self.runs.append(record)

    def record_event(self, record: ReplayEventAudit) -> None:
        self.events.append(record)

    def clear(self) -> None:
        self.runs.clear()
        self.events.clear()
