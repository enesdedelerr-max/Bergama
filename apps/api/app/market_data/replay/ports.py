"""Replay Engine ports (#308)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.orchestrator.context import PipelineContext
from app.market_data.orchestrator.ports import PublishPort, PublishResult
from app.market_data.replay.audit import ReplayEventAudit, ReplayRunAudit
from app.market_data.replay.checkpoint import ReplayCheckpoint
from app.market_data.replay.models import ReplayCursor, ReplayRecord, ReplayRequest


class ReplaySource(Protocol):
    """Bounded source of reconstructible Iceberg-backed replay records."""

    async def fetch(self, request: ReplayRequest) -> Sequence[ReplayRecord]:
        """Return records (pre-ordering optional). Must honor max_records bound."""
        ...

    async def aclose(self) -> None:
        """Release source resources. Idempotent."""
        ...


class CheckpointStore(Protocol):
    """Durable (or offline) checkpoint persistence."""

    async def load(self, replay_id: str) -> ReplayCheckpoint | None: ...

    async def save(self, checkpoint: ReplayCheckpoint) -> None: ...

    async def aclose(self) -> None: ...


class ReplayAuditSink(Protocol):
    def record_run(self, record: ReplayRunAudit) -> None: ...

    def record_event(self, record: ReplayEventAudit) -> None: ...

    def clear(self) -> None: ...


class ReplayCustomSink(Protocol):
    """Explicit typed custom sink — never auto-selected from environment."""

    async def publish(
        self,
        event: CanonicalMarketEvent,
        *,
        routing_key: str,
        context: PipelineContext,
    ) -> PublishResult: ...


class ReplaySleeper(Protocol):
    """Injectable delay for rate limiting (tests inject a no-op / advanceable sleeper)."""

    async def sleep(self, seconds: float) -> None: ...


# Re-export PublishPort for republish mode clarity.
__all__ = [
    "CheckpointStore",
    "PublishPort",
    "PublishResult",
    "ReplayAuditSink",
    "ReplayCursor",
    "ReplayCustomSink",
    "ReplaySleeper",
    "ReplaySource",
]
