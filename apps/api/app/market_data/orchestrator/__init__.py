"""Market Data Orchestrator (Sprint 3 Issue #305).

Canonical-event pipeline after connectors. No provider SDKs, Kafka, or Iceberg.
Uses bounded in-flight admission control and per-stream sequencing
(not a durable buffer or event-time reorderer).
"""

from __future__ import annotations

from app.market_data.orchestrator.admission import (
    AdmissionStats,
    AdmissionTimeoutError,
    InFlightAdmissionController,
)
from app.market_data.orchestrator.audit import AuditRecord, AuditSink, InMemoryAuditSink
from app.market_data.orchestrator.context import PipelineContext
from app.market_data.orchestrator.dedup import (
    BoundedDedupStore,
    DedupEntryState,
    DedupReserveOutcome,
    DedupReserveResult,
)
from app.market_data.orchestrator.errors import (
    OrchestratorClosedError,
    OrchestratorConfigurationError,
    OrchestratorError,
)
from app.market_data.orchestrator.metrics import OrchestratorMetrics
from app.market_data.orchestrator.pipeline import (
    MarketDataOrchestrator,
    ProcessResult,
    build_market_data_orchestrator,
)
from app.market_data.orchestrator.policies import PipelineDecision
from app.market_data.orchestrator.ports import (
    DryRunPublishPort,
    NoOpPublishPort,
    PublishPort,
    PublishResult,
)
from app.market_data.orchestrator.routing import routing_key_for
from app.market_data.orchestrator.sequencing import (
    PerStreamSequencer,
    StreamLease,
    StreamSequenceInfo,
)

__all__ = [
    "AdmissionStats",
    "AdmissionTimeoutError",
    "AuditRecord",
    "AuditSink",
    "BoundedDedupStore",
    "DedupEntryState",
    "DedupReserveOutcome",
    "DedupReserveResult",
    "DryRunPublishPort",
    "InFlightAdmissionController",
    "InMemoryAuditSink",
    "MarketDataOrchestrator",
    "NoOpPublishPort",
    "OrchestratorClosedError",
    "OrchestratorConfigurationError",
    "OrchestratorError",
    "OrchestratorMetrics",
    "PerStreamSequencer",
    "PipelineContext",
    "PipelineDecision",
    "ProcessResult",
    "PublishPort",
    "PublishResult",
    "StreamLease",
    "StreamSequenceInfo",
    "build_market_data_orchestrator",
    "routing_key_for",
]
