"""Insert-only Intelligence Run repository primitives (WS1).

Does not materialize ``PipelineResult``, compute canonical equality, or expose
product query/HTTP semantics (WS2/WS3).
"""

from __future__ import annotations

import uuid
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.intelligence_runs.errors import (
    IntelligenceRunIdentityConflictError,
    IntelligenceRunInvalidPersistedRepresentationError,
    IntelligenceRunPersistenceError,
    IntelligenceRunStorageUnavailableError,
)
from app.intelligence_runs.models import IntelligenceRunRecord

_FINGERPRINT_HEX_LEN = 64


class IntelligenceRunRepository(Protocol):
    def insert(self, record: IntelligenceRunRecord) -> IntelligenceRunRecord: ...

    def get_by_run_id(self, run_id: uuid.UUID) -> IntelligenceRunRecord | None: ...

    def get_by_logical_identity(
        self,
        fingerprint: str,
        snapshot_contract_version: str,
    ) -> IntelligenceRunRecord | None: ...


class SqlAlchemyIntelligenceRunRepository:
    """Synchronous SQLAlchemy implementation of insert-only persistence primitives."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def insert(self, record: IntelligenceRunRecord) -> IntelligenceRunRecord:
        self._validate_record(record)
        try:
            self._session.add(record)
            self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            raise IntelligenceRunIdentityConflictError(
                detail="logical identity or primary key conflict",
            ) from exc
        except OperationalError as exc:
            self._session.rollback()
            raise IntelligenceRunStorageUnavailableError(
                detail="storage unavailable during insert",
            ) from exc
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise IntelligenceRunPersistenceError(
                detail="unexpected persistence failure during insert",
            ) from exc
        return record

    def get_by_run_id(self, run_id: uuid.UUID) -> IntelligenceRunRecord | None:
        if not isinstance(run_id, uuid.UUID):
            raise IntelligenceRunInvalidPersistedRepresentationError(
                detail="run_id must be a UUID instance",
            )
        if run_id.version != 4:
            raise IntelligenceRunInvalidPersistedRepresentationError(
                detail="run_id must be UUID version 4",
            )
        try:
            return self._session.get(IntelligenceRunRecord, run_id)
        except OperationalError as exc:
            raise IntelligenceRunStorageUnavailableError(
                detail="storage unavailable during get_by_run_id",
            ) from exc
        except SQLAlchemyError as exc:
            raise IntelligenceRunPersistenceError(
                detail="unexpected persistence failure during get_by_run_id",
            ) from exc

    def get_by_logical_identity(
        self,
        fingerprint: str,
        snapshot_contract_version: str,
    ) -> IntelligenceRunRecord | None:
        if not isinstance(fingerprint, str) or not fingerprint:
            raise IntelligenceRunInvalidPersistedRepresentationError(
                detail=(
                    "logical identity lookup requires a non-null fingerprint; "
                    "admission_rejected NULL-fingerprint rows are addressed by run_id"
                ),
            )
        if len(fingerprint) != _FINGERPRINT_HEX_LEN or any(
            ch not in "0123456789abcdef" for ch in fingerprint
        ):
            raise IntelligenceRunInvalidPersistedRepresentationError(
                detail="fingerprint must be 64-char lowercase hex",
            )
        if not isinstance(snapshot_contract_version, str) or not snapshot_contract_version:
            raise IntelligenceRunInvalidPersistedRepresentationError(
                detail="snapshot_contract_version is required",
            )
        try:
            statement = select(IntelligenceRunRecord).where(
                IntelligenceRunRecord.pipeline_fingerprint == fingerprint,
                IntelligenceRunRecord.snapshot_contract_version == snapshot_contract_version,
            )
            return self._session.scalars(statement).one_or_none()
        except OperationalError as exc:
            raise IntelligenceRunStorageUnavailableError(
                detail="storage unavailable during get_by_logical_identity",
            ) from exc
        except SQLAlchemyError as exc:
            raise IntelligenceRunPersistenceError(
                detail="unexpected persistence failure during get_by_logical_identity",
            ) from exc

    @staticmethod
    def _validate_record(record: IntelligenceRunRecord) -> None:
        if not isinstance(record, IntelligenceRunRecord):
            raise IntelligenceRunInvalidPersistedRepresentationError(
                detail="record must be an IntelligenceRunRecord",
            )
        if not isinstance(record.run_id, uuid.UUID) or record.run_id.version != 4:
            raise IntelligenceRunInvalidPersistedRepresentationError(
                detail="run_id must be UUID4",
            )
