"""Backfill Engine ports (#309)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.market_data.backfill.audit import (
    BackfillEventAudit,
    BackfillRunAudit,
    BackfillSliceAudit,
)
from app.market_data.backfill.checkpoint import BackfillCheckpoint
from app.market_data.backfill.models import BackfillRequest, BackfillSlice
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.orchestrator.ports import PublishPort


class SliceFetchResult(Protocol):
    events: Sequence[CanonicalMarketEvent]
    may_have_more: bool
    request_count: int
    provider_cursor: dict[str, str]


class BackfillSource(Protocol):
    """Provider adapter wrapping an existing connector."""

    def build_slices(self, request: BackfillRequest) -> Sequence[BackfillSlice]: ...

    async def fetch_slice(
        self,
        slice_: BackfillSlice,
        request: BackfillRequest,
    ) -> tuple[Sequence[CanonicalMarketEvent], bool, int, dict[str, str]]:
        """Return (events, may_have_more, request_count, provider_cursor)."""
        ...

    async def aclose(self) -> None: ...


class BackfillCheckpointStore(Protocol):
    async def load(self, backfill_id: str) -> BackfillCheckpoint | None: ...

    async def save(self, checkpoint: BackfillCheckpoint) -> None: ...

    async def aclose(self) -> None: ...


class BackfillAuditSink(Protocol):
    def record_run(self, record: BackfillRunAudit) -> None: ...

    def record_slice(self, record: BackfillSliceAudit) -> None: ...

    def record_event(self, record: BackfillEventAudit) -> None: ...

    def clear(self) -> None: ...


class BackfillSleeper(Protocol):
    async def sleep(self, seconds: float) -> None: ...


class BackfillSourceRegistry(Protocol):
    def resolve(self, request: BackfillRequest) -> BackfillSource: ...


__all__ = [
    "BackfillAuditSink",
    "BackfillCheckpointStore",
    "BackfillSleeper",
    "BackfillSource",
    "BackfillSourceRegistry",
    "PublishPort",
]
