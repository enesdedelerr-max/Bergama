"""Intelligence Run product persistence package (Sprint 14).

WS1 owns PostgreSQL persistence substrate only. Materializer / query / HTTP
surfaces are deferred to later workstreams.
"""

from __future__ import annotations

from app.intelligence_runs.constants import (
    PERSISTENCE_SCHEMA_VERSION,
    SNAPSHOT_CONTRACT_VERSION,
)
from app.intelligence_runs.models import IntelligenceRunRecord
from app.intelligence_runs.repository import SqlAlchemyIntelligenceRunRepository

__all__ = [
    "PERSISTENCE_SCHEMA_VERSION",
    "SNAPSHOT_CONTRACT_VERSION",
    "IntelligenceRunRecord",
    "SqlAlchemyIntelligenceRunRepository",
]
