"""Unit tests for Intelligence Run ORM contract (WS1)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from app.intelligence_pipeline.policy import GLOBAL_OUTCOME_FAMILIES
from app.intelligence_runs.constants import (
    FAILURE_DETAIL_MAX_CHARS,
    PERSISTED_OUTCOMES,
    PERSISTENCE_SCHEMA_VERSION,
    SNAPSHOT_CONTRACT_VERSION,
)
from app.intelligence_runs.models import INTELLIGENCE_RUNS_TABLE, IntelligenceRunRecord


def test_frozen_version_constants() -> None:
    assert SNAPSHOT_CONTRACT_VERSION == "intelligence-run-productization.snapshot.v1"
    assert PERSISTENCE_SCHEMA_VERSION == "intelligence-run-productization.persistence.v1"


def test_persisted_outcomes_match_pipeline_policy() -> None:
    assert PERSISTED_OUTCOMES == GLOBAL_OUTCOME_FAMILIES
    assert len(PERSISTED_OUTCOMES) == 6


def test_table_name_and_columns() -> None:
    assert INTELLIGENCE_RUNS_TABLE == "intelligence_runs"
    columns = set(IntelligenceRunRecord.__table__.columns.keys())
    assert {
        "run_id",
        "pipeline_fingerprint",
        "as_of",
        "outcome",
        "failed_stage",
        "failure_error_type",
        "failure_detail",
        "bindings_json",
        "provenance_json",
        "stage_presence_json",
        "dashboard_snapshot_json",
        "human_review_snapshot_json",
        "ade_snapshot_json",
        "snapshot_contract_version",
        "persistence_schema_version",
        "persisted_at",
    } <= columns
    assert "age_seconds" not in columns


def test_record_accepts_uuid4_and_six_outcomes() -> None:
    for outcome in PERSISTED_OUTCOMES:
        record = IntelligenceRunRecord(
            run_id=uuid.uuid4(),
            pipeline_fingerprint=None if outcome == "admission_rejected" else "a" * 64,
            as_of=None if outcome == "admission_rejected" else datetime.now(UTC),
            outcome=outcome,
            provenance_json={"thin": True},
            stage_presence_json={"dashboard": "ABSENT"},
            snapshot_contract_version=SNAPSHOT_CONTRACT_VERSION,
            persistence_schema_version=PERSISTENCE_SCHEMA_VERSION,
            persisted_at=datetime.now(UTC),
        )
        assert record.outcome == outcome
        assert record.run_id.version == 4


def test_record_rejects_invalid_fingerprint() -> None:
    with pytest.raises(ValueError):
        IntelligenceRunRecord(
            run_id=uuid.uuid4(),
            pipeline_fingerprint="NOT-HEX",
            outcome="completed_dashboard",
            provenance_json={},
            stage_presence_json={},
            snapshot_contract_version=SNAPSHOT_CONTRACT_VERSION,
            persistence_schema_version=PERSISTENCE_SCHEMA_VERSION,
            persisted_at=datetime.now(UTC),
        )


def test_record_rejects_seventh_outcome() -> None:
    with pytest.raises(ValueError):
        IntelligenceRunRecord(
            run_id=uuid.uuid4(),
            pipeline_fingerprint="b" * 64,
            outcome="completed_mystery",
            provenance_json={},
            stage_presence_json={},
            snapshot_contract_version=SNAPSHOT_CONTRACT_VERSION,
            persistence_schema_version=PERSISTENCE_SCHEMA_VERSION,
            persisted_at=datetime.now(UTC),
        )


def test_record_rejects_oversized_failure_detail() -> None:
    with pytest.raises(ValueError):
        IntelligenceRunRecord(
            run_id=uuid.uuid4(),
            pipeline_fingerprint="c" * 64,
            outcome="required_stage_failed",
            failure_detail="x" * (FAILURE_DETAIL_MAX_CHARS + 1),
            provenance_json={},
            stage_presence_json={},
            snapshot_contract_version=SNAPSHOT_CONTRACT_VERSION,
            persistence_schema_version=PERSISTENCE_SCHEMA_VERSION,
            persisted_at=datetime.now(UTC),
        )


def test_unique_and_latest_indexes_declared() -> None:
    table = IntelligenceRunRecord.__table__
    constraint_names = {c.name for c in table.constraints}
    assert "uq_intelligence_runs_fingerprint_snapshot_version" in constraint_names
    index_names = {idx.name for idx in table.indexes}
    assert "ix_intelligence_runs_latest_dashboard" in index_names
