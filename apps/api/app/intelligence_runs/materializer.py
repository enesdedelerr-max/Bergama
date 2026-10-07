"""Intelligence Run materializer: PipelineResult → durable snapshot persistence (WS2).

Orchestrates validation, canonical equality, insert-only reuse/conflict, and
IntegrityError race recovery via a fresh session. Does not recompute pipeline
intelligence and does not expose HTTP/query surfaces.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session, sessionmaker

from app.intelligence_pipeline.models import PipelineResult
from app.intelligence_runs.constants import PERSISTENCE_SCHEMA_VERSION, SNAPSHOT_CONTRACT_VERSION
from app.intelligence_runs.database import session_scope
from app.intelligence_runs.errors import (
    IntelligenceRunIdentityConflictError,
    IntelligenceRunInvalidMaterializationError,
)
from app.intelligence_runs.models import IntelligenceRunRecord
from app.intelligence_runs.repository import SqlAlchemyIntelligenceRunRepository
from app.intelligence_runs.snapshot import (
    AuthoritativeSnapshot,
    build_authoritative_snapshot,
    canonical_snapshots_equal,
    reconstruct_authoritative_snapshot,
)


class IntelligenceRunMaterializer:
    """Application-layer materializer over WS1 insert-only repository primitives."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def materialize(self, result: PipelineResult) -> IntelligenceRunRecord:
        """Materialize a completed PipelineResult into an immutable durable run."""
        snapshot = build_authoritative_snapshot(result)
        fingerprint = snapshot.pipeline_fingerprint

        if fingerprint is None:
            return self._insert_new(snapshot)

        with session_scope(self._session_factory) as session:
            repository = SqlAlchemyIntelligenceRunRepository(session)
            existing = repository.get_by_logical_identity(
                fingerprint,
                SNAPSHOT_CONTRACT_VERSION,
            )
            if existing is not None:
                return self._reuse_or_conflict(existing, snapshot)

        try:
            with session_scope(self._session_factory) as session:
                repository = SqlAlchemyIntelligenceRunRepository(session)
                return self._insert_with_repository(repository, snapshot)
        except IntelligenceRunIdentityConflictError:
            return self._recover_after_unique_race(fingerprint, snapshot)

    def _recover_after_unique_race(
        self,
        fingerprint: str,
        snapshot: AuthoritativeSnapshot,
    ) -> IntelligenceRunRecord:
        """Re-open a fresh session after IntegrityError rollback and resolve race."""
        with session_scope(self._session_factory) as session:
            repository = SqlAlchemyIntelligenceRunRepository(session)
            existing = repository.get_by_logical_identity(
                fingerprint,
                SNAPSHOT_CONTRACT_VERSION,
            )
            if existing is None:
                raise IntelligenceRunIdentityConflictError(
                    detail="logical identity conflict without recoverable existing row",
                )
            return self._reuse_or_conflict(existing, snapshot)

    def _reuse_or_conflict(
        self,
        existing: IntelligenceRunRecord,
        snapshot: AuthoritativeSnapshot,
    ) -> IntelligenceRunRecord:
        existing_snapshot = reconstruct_authoritative_snapshot(existing)
        if canonical_snapshots_equal(existing_snapshot, snapshot):
            return existing
        raise IntelligenceRunIdentityConflictError(
            detail="materialization identity conflict: unequal authoritative snapshot",
        )

    def _insert_new(self, snapshot: AuthoritativeSnapshot) -> IntelligenceRunRecord:
        with session_scope(self._session_factory) as session:
            repository = SqlAlchemyIntelligenceRunRepository(session)
            return self._insert_with_repository(repository, snapshot)

    def _insert_with_repository(
        self,
        repository: SqlAlchemyIntelligenceRunRepository,
        snapshot: AuthoritativeSnapshot,
    ) -> IntelligenceRunRecord:
        return repository.insert(self._to_record(snapshot))

    @staticmethod
    def _to_record(snapshot: AuthoritativeSnapshot) -> IntelligenceRunRecord:
        if snapshot.snapshot_contract_version != SNAPSHOT_CONTRACT_VERSION:
            raise IntelligenceRunInvalidMaterializationError(
                detail="snapshot_contract_version mismatch on insert",
            )
        return IntelligenceRunRecord(
            run_id=uuid.uuid4(),
            pipeline_fingerprint=snapshot.pipeline_fingerprint,
            as_of=snapshot.as_of,
            outcome=snapshot.outcome,
            failed_stage=snapshot.failed_stage,
            failure_error_type=snapshot.failure_error_type,
            failure_detail=snapshot.failure_detail,
            bindings_json=snapshot.bindings,
            provenance_json=snapshot.provenance,
            stage_presence_json=dict(snapshot.stage_presence),
            dashboard_snapshot_json=snapshot.dashboard_snapshot,
            human_review_snapshot_json=snapshot.human_review_snapshot,
            ade_snapshot_json=snapshot.ade_snapshot,
            snapshot_contract_version=SNAPSHOT_CONTRACT_VERSION,
            persistence_schema_version=PERSISTENCE_SCHEMA_VERSION,
            persisted_at=datetime.now(UTC),
        )
