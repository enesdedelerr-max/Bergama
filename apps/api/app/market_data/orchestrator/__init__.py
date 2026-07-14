"""Market Data Orchestrator (Sprint 3 Issue #305).

Canonical-event pipeline after connectors. No provider SDKs, Kafka, or Iceberg.
Uses bounded in-flight admission control (not a durable buffer).
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
    OrchestratorConfigurationError,
    OrchestratorError,
)
from app.market_data.orchestrator.ordering import OrderingDecision, OrderingTracker
from app.market_data.orchestrator.pipeline import (
    MarketDataOrchestrator,
    PipelineMetrics,
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
    "OrderingDecision",
    "OrderingTracker",
    "OrchestratorConfigurationError",
    "OrchestratorError",
    "PipelineContext",
    "PipelineDecision",
    "PipelineMetrics",
    "PublishPort",
    "PublishResult",
    "build_market_data_orchestrator",
    "routing_key_for",
]
