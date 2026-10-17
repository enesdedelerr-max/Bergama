"""PostgreSQL integration: atomic analyst co-persistence with Intelligence Runs (WS2)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from alembic import command
from alembic.config import Config
from app.intelligence_pipeline import PipelineOutcome, run_intelligence_pipeline
from app.intelligence_runs.constants import (
    PERSISTENCE_SCHEMA_VERSION_V2,
    SNAPSHOT_CONTRACT_VERSION_V2,
)
from app.intelligence_runs.database import create_session_factory, create_sync_engine, session_scope
from app.intelligence_runs.errors import IntelligenceRunInvalidMaterializationError
from app.intelligence_runs.materializer import IntelligenceRunMaterializer
from app.intelligence_runs.repository import SqlAlchemyIntelligenceRunRepository
from app.intelligence_runs.snapshot import (
    build_authoritative_snapshot,
    canonical_snapshots_equal,
    reconstruct_authoritative_snapshot,
)
from sqlalchemy import Engine, text
from sqlalchemy.orm import sessionmaker
from tests.unit.test_intelligence_pipeline_core import VALID_ATTESTATION, _valid_request

pytestmark = pytest.mark.postgres_integration

_API_ROOT = Path(__file__).resolve().parents[2]


def _require_database_url() -> str:
    url = os.environ.get("BERGAMA_DATABASE__URL", "").strip()
    if not url:
        pytest.skip("BERGAMA_DATABASE__URL required for PostgreSQL analyst co-persist tests")
    return url


def _alembic_config(url: str) -> Config:
    cfg = Config(str(_API_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_API_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    os.environ["BERGAMA_DATABASE__URL"] = url
    return cfg


@pytest.fixture(scope="module")
def engine() -> Iterator[Engine]:
    url = _require_database_url()
    eng = create_sync_engine(url)
    command.upgrade(_alembic_config(url), "head")
    yield eng
    eng.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> Iterator[sessionmaker]:
    factory = create_session_factory(engine)
    with session_scope(factory) as session:
        session.execute(text("DELETE FROM intelligence_runs"))
        session.commit()
    yield factory
    with session_scope(factory) as session:
        session.execute(text("DELETE FROM intelligence_runs"))
        session.commit()


def test_atomic_copersist_completed_dashboard(session_factory: sessionmaker) -> None:
    materializer = IntelligenceRunMaterializer(session_factory)
    result = run_intelligence_pipeline(_valid_request())
    snapshot = build_authoritative_snapshot(result)
    record = materializer.materialize(result)
    assert record.snapshot_contract_version == SNAPSHOT_CONTRACT_VERSION_V2
    assert record.persistence_schema_version == PERSISTENCE_SCHEMA_VERSION_V2
    assert record.dashboard_snapshot_json is not None
    assert record.analyst_snapshot_json is not None
    assert record.analyst_snapshot_json["evaluation_state"] is not None
    reconstructed = reconstruct_authoritative_snapshot(record)
    assert canonical_snapshots_equal(snapshot, reconstructed)
    assert reconstructed.analyst_snapshot == record.analyst_snapshot_json


def test_ineligible_outcomes_persist_null_analyst(session_factory: sessionmaker) -> None:
    materializer = IntelligenceRunMaterializer(session_factory)
    rejected = materializer.materialize(
        run_intelligence_pipeline(_valid_request(hr_requested=True, hr_attestation=None))
    )
    assert rejected.outcome == PipelineOutcome.ADMISSION_REJECTED.value
    assert rejected.analyst_snapshot_json is None

    monkey = pytest.MonkeyPatch()
    monkey.setattr(
        "app.intelligence_pipeline.orchestrator.scan_gaps",
        MagicMock(side_effect=ValueError("gap_fail")),
    )
    try:
        failed = materializer.materialize(run_intelligence_pipeline(_valid_request()))
    finally:
        monkey.undo()
    assert failed.outcome == PipelineOutcome.REQUIRED_STAGE_FAILED.value
    assert failed.analyst_snapshot_json is None


def test_idempotent_reuse_includes_analyst_equality(session_factory: sessionmaker) -> None:
    materializer = IntelligenceRunMaterializer(session_factory)
    result = run_intelligence_pipeline(_valid_request())
    first = materializer.materialize(result)
    second = materializer.materialize(result)
    assert first.run_id == second.run_id
    assert first.analyst_snapshot_json == second.analyst_snapshot_json


def test_analyst_payload_conflict_on_tamper(session_factory: sessionmaker) -> None:
    materializer = IntelligenceRunMaterializer(session_factory)
    result = run_intelligence_pipeline(_valid_request())
    record = materializer.materialize(result)
    fingerprint = record.pipeline_fingerprint
    assert fingerprint is not None
    with session_scope(session_factory) as session:
        repo = SqlAlchemyIntelligenceRunRepository(session)
        existing = repo.get_by_logical_identity(fingerprint, SNAPSHOT_CONTRACT_VERSION_V2)
        assert existing is not None
        assert existing.analyst_snapshot_json is not None
        existing.analyst_snapshot_json = {
            **existing.analyst_snapshot_json,
            "evaluation_state": "ABSTAIN",
        }
        session.flush()
    from app.intelligence_runs.errors import IntelligenceRunIdentityConflictError

    with pytest.raises(IntelligenceRunIdentityConflictError):
        materializer.materialize(result)


def test_projection_failure_does_not_partial_commit(
    session_factory: sessionmaker,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.premarket_analyst.errors import PremarketAnalystFailClosedError

    def boom(_request: object) -> object:
        raise PremarketAnalystFailClosedError("blocked")

    monkeypatch.setattr("app.intelligence_runs.snapshot.project_analyst", boom)
    materializer = IntelligenceRunMaterializer(session_factory)
    with pytest.raises(IntelligenceRunInvalidMaterializationError):
        materializer.materialize(run_intelligence_pipeline(_valid_request()))
    with session_scope(session_factory) as session:
        count = session.execute(text("SELECT COUNT(*) FROM intelligence_runs")).scalar_one()
    assert count == 0


def test_ade_accept_copersists_analyst(session_factory: sessionmaker) -> None:
    materializer = IntelligenceRunMaterializer(session_factory)
    result = run_intelligence_pipeline(
        _valid_request(
            hr_requested=True,
            ade_requested=True,
            hr_attestation=VALID_ATTESTATION,
        )
    )
    record = materializer.materialize(result)
    assert record.outcome == PipelineOutcome.COMPLETED_ADE_ACCEPT.value
    assert record.ade_snapshot_json is not None
    assert record.analyst_snapshot_json is not None
