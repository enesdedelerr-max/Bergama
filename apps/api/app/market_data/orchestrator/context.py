"""Immutable PipelineContext for market-data orchestration (#305)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any

from app.core.clock import Clock
from app.market_data.envelope import CanonicalMarketEvent
from app.market_data.orchestrator.audit import AuditRecord
from app.market_data.orchestrator.policies import PipelineDecision
from app.market_data.quality import DataQualityFlags


@dataclass(frozen=True, slots=True)
class PipelineContext:
    """Immutable snapshot of pipeline state for one event.

    Stages return a new context via ``evolve``; never mutate in place.
    """

    event: CanonicalMarketEvent
    dedup_key: str | None
    idempotency_key: str | None
    routing_key: str | None
    decision: PipelineDecision
    quality: DataQualityFlags
    received_at: datetime
    pipeline_clock: Clock
    correlation_id: str | None
    audit: tuple[AuditRecord, ...]
    metadata: Mapping[str, str] = field(default_factory=dict)
    reason: str | None = None
    order_scope: str | None = None
    order_sequence: int | None = None
    out_of_order: bool = False

    def evolve(self, **changes: Any) -> PipelineContext:
        """Return a new context with ``changes`` applied."""
        if "metadata" in changes and changes["metadata"] is not None:
            changes["metadata"] = dict(changes["metadata"])
        if "audit" in changes and changes["audit"] is not None:
            changes["audit"] = tuple(changes["audit"])
        return replace(self, **changes)

    def with_audit(self, record: AuditRecord) -> PipelineContext:
        return self.evolve(audit=(*self.audit, record))
