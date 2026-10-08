"""Unit tests for Intelligence Run query service (WS3)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest
from app.core.clock import FixedClock
from app.intelligence_pipeline import PipelineOutcome, run_intelligence_pipeline
from app.intelligence_runs.constants import (
    PERSISTENCE_SCHEMA_VERSION,
    SNAPSHOT_CONTRACT_VERSION,
)
from app.intelligence_runs.errors import IntelligenceRunStorageUnavailableError
from app.intelligence_runs.models import IntelligenceRunRecord
from app.intelligence_runs.product_errors import IntelligenceRunProductError
from app.intelligence_runs.query_service import IntelligenceRunQueryService
from app.intelligence_runs.snapshot import build_authoritative_snapshot
from tests.unit.test_intelligence_pipeline_core import VALID_ATTESTATION, _valid_request

FIXED_NOW = datetime(2026, 10, 7, 18, 0, tzinfo=UTC)


def _record_from_pipeline(**kwargs: Any) -> IntelligenceRunRecord:
    result = run_intelligence_pipeline(_valid_request(**kwargs))
    snapshot = build_authoritative_snapshot(result)
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
        persisted_at=FIXED_NOW - timedelta(seconds=90),
    )


def _service_with_record(record: IntelligenceRunRecord | None) -> IntelligenceRunQueryService:
    session = MagicMock()
    service = IntelligenceRunQueryService(session=session, clock=FixedClock(FIXED_NOW))
    repo = MagicMock()
    repo.get_by_run_id.return_value = record
    repo.get_by_logical_identity.return_value = record
    repo.get_latest_dashboard_storage_candidate.return_value = record
    service._repository = repo  # noqa: SLF001 — unit isolation
    return service


def test_run_id_validation_rejects_malformed_and_non_uuid4() -> None:
    service = _service_with_record(None)
    with pytest.raises(IntelligenceRunProductError) as exc:
        service.get_run_by_id("not-a-uuid")
    assert exc.value.code == "intelligence.runs.invalid_identifier"
    assert exc.value.status_code == 400

    uuid1 = uuid.uuid1()
    with pytest.raises(IntelligenceRunProductError) as exc:
        service.get_run_by_id(str(uuid1))
    assert exc.value.code == "intelligence.runs.invalid_identifier"


def test_fingerprint_validation_and_current_version_lookup() -> None:
    record = _record_from_pipeline()
    service = _service_with_record(record)
    assert record.pipeline_fingerprint is not None
    read = service.get_run_by_fingerprint(record.pipeline_fingerprint)
    assert read.run_id == str(record.run_id)
    service._repository.get_by_logical_identity.assert_called_once_with(  # noqa: SLF001
        record.pipeline_fingerprint,
        SNAPSHOT_CONTRACT_VERSION,
    )
    with pytest.raises(IntelligenceRunProductError) as exc:
        service.get_run_by_fingerprint("ABC")
    assert exc.value.code == "intelligence.runs.invalid_identifier"
    with pytest.raises(IntelligenceRunProductError) as exc:
        service.get_run_by_fingerprint("A" * 64)
    assert exc.value.code == "intelligence.runs.invalid_identifier"
    assert exc.value.status_code == 400


def test_missing_run_returns_not_found() -> None:
    service = _service_with_record(None)
    with pytest.raises(IntelligenceRunProductError) as exc:
        service.get_run_by_id(str(uuid.uuid4()))
    assert exc.value.code == "intelligence.runs.run_not_found"
    assert exc.value.status_code == 404


def test_unsupported_version_gated_before_reconstruct() -> None:
    record = _record_from_pipeline()
    # Bypass ORM @validates by writing the instrumented attribute dict.
    record.__dict__["snapshot_contract_version"] = "intelligence-run-productization.snapshot.v0"
    service = _service_with_record(record)
    with pytest.raises(IntelligenceRunProductError) as exc:
        service.get_run_by_id(str(record.run_id))
    assert exc.value.code == "intelligence.runs.unsupported_snapshot_contract"
    assert exc.value.status_code == 409


def test_corrupt_persisted_snapshot_maps_to_500() -> None:
    record = _record_from_pipeline()
    record.stage_presence_json = {"dashboard": "PRESENT"}  # incomplete keys
    service = _service_with_record(record)
    with pytest.raises(IntelligenceRunProductError) as exc:
        service.get_run_by_id(str(record.run_id))
    assert exc.value.code == "intelligence.runs.corrupt_persisted_snapshot"
    assert exc.value.status_code == 500


def test_stage_absence_and_success() -> None:
    dashboard_only = _record_from_pipeline()
    service = _service_with_record(dashboard_only)
    with pytest.raises(IntelligenceRunProductError) as exc:
        service.get_human_review(str(dashboard_only.run_id))
    assert exc.value.code == "intelligence.runs.stage_not_present"

    hr = _record_from_pipeline(hr_requested=True, hr_attestation=VALID_ATTESTATION)
    service = _service_with_record(hr)
    body = service.get_human_review(str(hr.run_id))
    assert body.human_review is not None


def test_ade_success_excludes_private_payload() -> None:
    record = _record_from_pipeline(
        hr_requested=True,
        ade_requested=True,
        hr_attestation=VALID_ATTESTATION,
    )
    service = _service_with_record(record)
    body = service.get_ade(str(record.run_id))
    dumped = body.model_dump(mode="json")
    assert "recorded_attestation_payload" not in str(dumped)


def test_age_seconds_deterministic_and_clamped() -> None:
    record = _record_from_pipeline()
    record.persisted_at = FIXED_NOW + timedelta(seconds=30)
    service = _service_with_record(record)
    read = service.get_run_by_id(str(record.run_id))
    assert read.age_seconds == 0

    record.persisted_at = FIXED_NOW - timedelta(seconds=125)
    service = _service_with_record(record)
    read = service.get_run_by_id(str(record.run_id))
    assert read.age_seconds == 125


def test_latest_fail_closed_no_skip_on_corrupt() -> None:
    record = _record_from_pipeline()
    record.dashboard_snapshot_json = {"broken": True}
    service = _service_with_record(record)
    with pytest.raises(IntelligenceRunProductError) as exc:
        service.get_latest_dashboard_capable()
    assert exc.value.status_code == 500
    # Repository called exactly once — no skip fetch.
    assert service._repository.get_latest_dashboard_storage_candidate.call_count == 1  # noqa: SLF001


def test_latest_fail_closed_no_skip_on_unsupported() -> None:
    record = _record_from_pipeline()
    record.__dict__["snapshot_contract_version"] = "other.v0"
    service = _service_with_record(record)
    with pytest.raises(IntelligenceRunProductError) as exc:
        service.get_latest_dashboard_capable()
    assert exc.value.code == "intelligence.runs.unsupported_snapshot_contract"
    assert service._repository.get_latest_dashboard_storage_candidate.call_count == 1  # noqa: SLF001


def test_latest_empty_is_not_found() -> None:
    service = _service_with_record(None)
    with pytest.raises(IntelligenceRunProductError) as exc:
        service.get_latest_dashboard_capable()
    assert exc.value.code == "intelligence.runs.run_not_found"


def test_storage_unavailable_maps_to_503() -> None:
    service = _service_with_record(_record_from_pipeline())
    service._repository.get_by_run_id.side_effect = IntelligenceRunStorageUnavailableError(  # noqa: SLF001
        detail="down",
    )
    with pytest.raises(IntelligenceRunProductError) as exc:
        service.get_run_by_id(str(uuid.uuid4()))
    assert exc.value.code == "intelligence.runs.storage_unavailable"
    assert exc.value.status_code == 503


def test_query_service_has_no_write_methods() -> None:
    service = IntelligenceRunQueryService(session=MagicMock(), clock=FixedClock(FIXED_NOW))
    for name in ("insert", "update", "delete", "upsert", "materialize"):
        assert not hasattr(service, name)


def test_completed_dashboard_outcome() -> None:
    record = _record_from_pipeline()
    assert record.outcome == PipelineOutcome.COMPLETED_DASHBOARD.value
    service = _service_with_record(record)
    read = service.get_run_by_id(str(record.run_id))
    assert read.dashboard is not None
    assert read.stage_presence["dashboard"] == "PRESENT"
