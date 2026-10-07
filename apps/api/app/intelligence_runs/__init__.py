"""Intelligence Run product persistence package (Sprint 14).

WS1 owns PostgreSQL persistence substrate.
WS2 owns PipelineResult materialization / snapshot / canonical equality.
Query / HTTP surfaces remain deferred to WS3.
"""

from __future__ import annotations

from app.intelligence_runs.constants import (
    PERSISTENCE_SCHEMA_VERSION,
    SNAPSHOT_CONTRACT_VERSION,
)
from app.intelligence_runs.materializer import IntelligenceRunMaterializer
from app.intelligence_runs.models import IntelligenceRunRecord
from app.intelligence_runs.repository import SqlAlchemyIntelligenceRunRepository
from app.intelligence_runs.snapshot import AuthoritativeSnapshot, build_authoritative_snapshot

__all__ = [
    "PERSISTENCE_SCHEMA_VERSION",
    "SNAPSHOT_CONTRACT_VERSION",
    "AuthoritativeSnapshot",
    "IntelligenceRunMaterializer",
    "IntelligenceRunRecord",
    "SqlAlchemyIntelligenceRunRepository",
    "build_authoritative_snapshot",
]
