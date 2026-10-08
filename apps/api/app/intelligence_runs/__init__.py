"""Intelligence Run product persistence and read package (Sprint 14).

WS1 owns PostgreSQL persistence substrate.
WS2 owns PipelineResult materialization / snapshot / canonical equality.
WS3 owns query service and authenticated GET product routes.
"""

from __future__ import annotations

from app.intelligence_runs.constants import (
    PERSISTENCE_SCHEMA_VERSION,
    SNAPSHOT_CONTRACT_VERSION,
)
from app.intelligence_runs.materializer import IntelligenceRunMaterializer
from app.intelligence_runs.models import IntelligenceRunRecord
from app.intelligence_runs.query_service import IntelligenceRunQueryService
from app.intelligence_runs.repository import SqlAlchemyIntelligenceRunRepository
from app.intelligence_runs.snapshot import AuthoritativeSnapshot, build_authoritative_snapshot

__all__ = [
    "PERSISTENCE_SCHEMA_VERSION",
    "SNAPSHOT_CONTRACT_VERSION",
    "AuthoritativeSnapshot",
    "IntelligenceRunMaterializer",
    "IntelligenceRunQueryService",
    "IntelligenceRunRecord",
    "SqlAlchemyIntelligenceRunRepository",
    "build_authoritative_snapshot",
]
