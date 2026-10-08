"""Read-only Intelligence Run query service (WS3).

No materialization, recomputation, ADE invocation, or writes.
"""

from __future__ import annotations

import math
import re
import uuid
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.dashboard.models import DashboardPresentationOutput
from app.human_review.models import HumanReviewOutput
from app.intelligence_pipeline.policy import STAGE_ADE, STAGE_DASHBOARD, STAGE_HUMAN_REVIEW
from app.intelligence_runs.constants import (
    PIPELINE_FINGERPRINT_LENGTH,
    SNAPSHOT_CONTRACT_VERSION,
)
from app.intelligence_runs.errors import (
    IntelligenceRunInvalidPersistedRepresentationError,
    IntelligenceRunPersistenceError,
    IntelligenceRunStorageUnavailableError,
)
from app.intelligence_runs.models import IntelligenceRunRecord
from app.intelligence_runs.product_errors import (
    corrupt_persisted_snapshot,
    invalid_identifier,
    run_not_found,
    stage_not_present,
    storage_unavailable,
    unsupported_snapshot_contract,
)
from app.intelligence_runs.repository import SqlAlchemyIntelligenceRunRepository
from app.intelligence_runs.snapshot import (
    AuthoritativeSnapshot,
    StagePresenceStatus,
    reconstruct_authoritative_snapshot,
)
from app.schemas.intelligence_runs import (
    AdeProductSnapshotRead,
    IntelligenceRunAdeRead,
    IntelligenceRunDashboardRead,
    IntelligenceRunHumanReviewRead,
    IntelligenceRunRead,
)

_FINGERPRINT_RE = re.compile(rf"^[0-9a-f]{{{PIPELINE_FINGERPRINT_LENGTH}}}$")
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_FORBIDDEN_ADE_PAYLOAD_KEY = "recorded_attestation_payload"


class IntelligenceRunQueryService:
    """Application-layer read/query orchestration over insert-only persistence."""

    def __init__(self, *, session: Session, clock: Clock) -> None:
        self._repository = SqlAlchemyIntelligenceRunRepository(session)
        self._clock = clock

    def get_run_by_id(self, run_id_raw: str) -> IntelligenceRunRead:
        run_id = self._parse_run_id(run_id_raw)
        record = self._load_by_run_id(run_id)
        return self._to_run_read(record)

    def get_run_by_fingerprint(self, fingerprint_raw: str) -> IntelligenceRunRead:
        fingerprint = self._parse_fingerprint(fingerprint_raw)
        record = self._load_by_fingerprint(fingerprint)
        return self._to_run_read(record)

    def get_latest_dashboard_capable(self) -> IntelligenceRunRead:
        try:
            candidate = self._repository.get_latest_dashboard_storage_candidate()
        except IntelligenceRunStorageUnavailableError as exc:
            raise storage_unavailable() from exc
        except IntelligenceRunPersistenceError as exc:
            raise storage_unavailable() from exc
        if candidate is None:
            raise run_not_found(detail="no dashboard-capable intelligence run")
        # Single candidate only — unsupported/corrupt must fail closed without skip.
        return self._to_run_read(candidate, require_dashboard_capable=True)

    def get_dashboard(self, run_id_raw: str) -> IntelligenceRunDashboardRead:
        run_id = self._parse_run_id(run_id_raw)
        record = self._load_by_run_id(run_id)
        snapshot = self._validated_snapshot(record)
        status = snapshot.stage_presence.get(STAGE_DASHBOARD)
        if status != StagePresenceStatus.PRESENT.value:
            raise stage_not_present(stage=STAGE_DASHBOARD)
        dashboard = self._parse_dashboard(snapshot.dashboard_snapshot)
        return IntelligenceRunDashboardRead(
            run_id=str(record.run_id),
            dashboard=dashboard,
        )

    def get_human_review(self, run_id_raw: str) -> IntelligenceRunHumanReviewRead:
        run_id = self._parse_run_id(run_id_raw)
        record = self._load_by_run_id(run_id)
        snapshot = self._validated_snapshot(record)
        status = snapshot.stage_presence.get(STAGE_HUMAN_REVIEW)
        if status != StagePresenceStatus.PRESENT.value:
            raise stage_not_present(stage=STAGE_HUMAN_REVIEW)
        human_review = self._parse_human_review(snapshot.human_review_snapshot)
        return IntelligenceRunHumanReviewRead(
            run_id=str(record.run_id),
            human_review=human_review,
        )

    def get_ade(self, run_id_raw: str) -> IntelligenceRunAdeRead:
        run_id = self._parse_run_id(run_id_raw)
        record = self._load_by_run_id(run_id)
        snapshot = self._validated_snapshot(record)
        status = snapshot.stage_presence.get(STAGE_ADE)
        if status not in {
            StagePresenceStatus.PRESENT.value,
            StagePresenceStatus.ABSTAINED.value,
        }:
            raise stage_not_present(stage=STAGE_ADE)
        ade = self._parse_ade(snapshot.ade_snapshot)
        return IntelligenceRunAdeRead(run_id=str(record.run_id), ade=ade)

    def _load_by_run_id(self, run_id: uuid.UUID) -> IntelligenceRunRecord:
        try:
            record = self._repository.get_by_run_id(run_id)
        except IntelligenceRunInvalidPersistedRepresentationError as exc:
            raise invalid_identifier(detail="run_id must be a UUID4") from exc
        except IntelligenceRunStorageUnavailableError as exc:
            raise storage_unavailable() from exc
        except IntelligenceRunPersistenceError as exc:
            raise storage_unavailable() from exc
        if record is None:
            raise run_not_found()
        return record

    def _load_by_fingerprint(self, fingerprint: str) -> IntelligenceRunRecord:
        try:
            record = self._repository.get_by_logical_identity(
                fingerprint,
                SNAPSHOT_CONTRACT_VERSION,
            )
        except IntelligenceRunInvalidPersistedRepresentationError as exc:
            raise invalid_identifier(detail="fingerprint must be 64-char lowercase hex") from exc
        except IntelligenceRunStorageUnavailableError as exc:
            raise storage_unavailable() from exc
        except IntelligenceRunPersistenceError as exc:
            raise storage_unavailable() from exc
        if record is None:
            raise run_not_found()
        return record

    def _to_run_read(
        self,
        record: IntelligenceRunRecord,
        *,
        require_dashboard_capable: bool = False,
    ) -> IntelligenceRunRead:
        snapshot = self._validated_snapshot(record)
        if require_dashboard_capable:
            status = snapshot.stage_presence.get(STAGE_DASHBOARD)
            if status != StagePresenceStatus.PRESENT.value or snapshot.dashboard_snapshot is None:
                raise corrupt_persisted_snapshot(
                    detail="latest dashboard candidate failed semantic eligibility",
                )
        dashboard = (
            self._parse_dashboard(snapshot.dashboard_snapshot)
            if snapshot.dashboard_snapshot is not None
            else None
        )
        human_review = (
            self._parse_human_review(snapshot.human_review_snapshot)
            if snapshot.human_review_snapshot is not None
            else None
        )
        ade = self._parse_ade(snapshot.ade_snapshot) if snapshot.ade_snapshot is not None else None
        return IntelligenceRunRead(
            run_id=str(record.run_id),
            pipeline_fingerprint=snapshot.pipeline_fingerprint,
            as_of=snapshot.as_of,
            persisted_at=record.persisted_at,
            snapshot_contract_version=record.snapshot_contract_version,
            persistence_schema_version=record.persistence_schema_version,
            age_seconds=self._age_seconds(record),
            outcome=snapshot.outcome,
            failed_stage=snapshot.failed_stage,
            failure_error_type=snapshot.failure_error_type,
            failure_detail=snapshot.failure_detail,
            bindings=snapshot.bindings,
            provenance=dict(snapshot.provenance),
            stage_presence=dict(snapshot.stage_presence),
            dashboard=dashboard,
            human_review=human_review,
            ade=ade,
        )

    def _validated_snapshot(self, record: IntelligenceRunRecord) -> AuthoritativeSnapshot:
        version = record.snapshot_contract_version
        if version != SNAPSHOT_CONTRACT_VERSION:
            raise unsupported_snapshot_contract(version=version)
        try:
            return reconstruct_authoritative_snapshot(record)
        except IntelligenceRunInvalidPersistedRepresentationError as exc:
            raise corrupt_persisted_snapshot(
                detail="corrupt or incomplete persisted authoritative snapshot",
            ) from exc

    def _age_seconds(self, record: IntelligenceRunRecord) -> int:
        delta = self._clock.now() - record.persisted_at
        return max(0, math.floor(delta.total_seconds()))

    @staticmethod
    def _parse_run_id(raw: str) -> uuid.UUID:
        text = raw.strip()
        if not _UUID_RE.fullmatch(text):
            raise invalid_identifier(detail="run_id must be a hyphenated UUID4")
        try:
            value = uuid.UUID(text)
        except ValueError as exc:
            raise invalid_identifier(detail="run_id must be a UUID") from exc
        if value.version != 4:
            raise invalid_identifier(detail="run_id must be UUID version 4")
        return value

    @staticmethod
    def _parse_fingerprint(raw: str) -> str:
        text = raw.strip()
        if not _FINGERPRINT_RE.fullmatch(text):
            raise invalid_identifier(detail="fingerprint must be 64-char lowercase hex")
        return text

    @staticmethod
    def _parse_dashboard(payload: dict[str, Any] | None) -> DashboardPresentationOutput:
        if payload is None:
            raise corrupt_persisted_snapshot(detail="dashboard snapshot missing")
        try:
            return DashboardPresentationOutput.model_validate(payload)
        except ValidationError as exc:
            raise corrupt_persisted_snapshot(detail="dashboard snapshot invalid") from exc

    @staticmethod
    def _parse_human_review(payload: dict[str, Any] | None) -> HumanReviewOutput:
        if payload is None:
            raise corrupt_persisted_snapshot(detail="human review snapshot missing")
        try:
            return HumanReviewOutput.model_validate(payload)
        except ValidationError as exc:
            raise corrupt_persisted_snapshot(detail="human review snapshot invalid") from exc

    @staticmethod
    def _parse_ade(payload: dict[str, Any] | None) -> AdeProductSnapshotRead:
        if payload is None:
            raise corrupt_persisted_snapshot(detail="ade snapshot missing")
        if _contains_forbidden_ade_payload(payload):
            raise corrupt_persisted_snapshot(
                detail="ade snapshot contains forbidden recorded_attestation_payload",
            )
        try:
            return AdeProductSnapshotRead.model_validate(payload)
        except ValidationError as exc:
            raise corrupt_persisted_snapshot(detail="ade snapshot invalid") from exc


def _contains_forbidden_ade_payload(payload: object) -> bool:
    if isinstance(payload, dict):
        if _FORBIDDEN_ADE_PAYLOAD_KEY in payload:
            return True
        return any(_contains_forbidden_ade_payload(value) for value in payload.values())
    if isinstance(payload, list | tuple):
        return any(_contains_forbidden_ade_payload(item) for item in payload)
    return False


__all__ = ["IntelligenceRunQueryService"]
