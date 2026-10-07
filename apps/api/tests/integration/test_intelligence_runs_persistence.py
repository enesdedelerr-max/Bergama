"""PostgreSQL integration tests for Intelligence Run repository (WS1)."""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.intelligence_runs.constants import (
    PERSISTENCE_SCHEMA_VERSION,
    SNAPSHOT_CONTRACT_VERSION,
)
from app.intelligence_runs.database import create_session_factory, create_sync_engine, session_scope
from app.intelligence_runs.errors import IntelligenceRunIdentityConflictError
from app.intelligence_runs.models import IntelligenceRunRecord
from app.intelligence_runs.repository import SqlAlchemyIntelligenceRunRepository
from sqlalchemy import Engine, inspect, text
from sqlalchemy.orm import Session

pytestmark = pytest.mark.postgres_integration

_API_ROOT = Path(__file__).resolve().parents[2]


def _require_database_url() -> str:
    url = os.environ.get("BERGAMA_DATABASE__URL", "").strip()
    if not url:
        pytest.skip("BERGAMA_DATABASE__URL required for PostgreSQL integration tests")
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
def repository_session(
    engine: Engine,
) -> Iterator[tuple[Session, SqlAlchemyIntelligenceRunRepository]]:
    factory = create_session_factory(engine)
    with session_scope(factory) as session:
        session.execute(text("DELETE FROM intelligence_runs"))
        session.commit()
    with session_scope(factory) as session:
        yield session, SqlAlchemyIntelligenceRunRepository(session)


def _stage_presence(*, dashboard: str = "ABSENT") -> dict[str, str]:
    return {
        "watchlist": "NOT_EXECUTED",
        "gap": "NOT_EXECUTED",
        "catalyst": "NOT_EXECUTED",
        "score": "NOT_EXECUTED",
        "briefing": "NOT_EXECUTED",
        "dashboard": dashboard,
        "human_review": "ABSENT",
        "ade": "ABSENT",
    }


def _base_record(**overrides: object) -> IntelligenceRunRecord:
    payload: dict[str, object] = {
        "run_id": uuid.uuid4(),
        "pipeline_fingerprint": "a" * 64,
        "as_of": datetime(2026, 10, 7, 12, 0, tzinfo=UTC),
        "outcome": "completed_dashboard",
        "failed_stage": None,
        "failure_error_type": None,
        "failure_detail": None,
        "bindings_json": {"policy_version_id": "intelligence-pipeline.policy.v1"},
        "provenance_json": {"pipeline_fingerprint": "a" * 64},
        "stage_presence_json": _stage_presence(dashboard="PRESENT"),
        "dashboard_snapshot_json": {"kind": "dashboard", "bounded": True},
        "human_review_snapshot_json": None,
        "ade_snapshot_json": None,
        "snapshot_contract_version": SNAPSHOT_CONTRACT_VERSION,
        "persistence_schema_version": PERSISTENCE_SCHEMA_VERSION,
        "persisted_at": datetime(2026, 10, 7, 12, 5, tzinfo=UTC),
    }
    payload.update(overrides)
    return IntelligenceRunRecord(**payload)  # type: ignore[arg-type]


def test_insert_and_get_by_run_id(
    repository_session: tuple[Session, SqlAlchemyIntelligenceRunRepository],
) -> None:
    session, repo = repository_session
    record = _base_record()
    inserted = repo.insert(record)
    session.commit()
    loaded = repo.get_by_run_id(inserted.run_id)
    assert loaded is not None
    assert loaded.run_id == inserted.run_id
    assert loaded.outcome == "completed_dashboard"
    assert loaded.dashboard_snapshot_json == {"kind": "dashboard", "bounded": True}
    assert loaded.run_id.version == 4


def test_get_by_logical_identity(
    repository_session: tuple[Session, SqlAlchemyIntelligenceRunRepository],
) -> None:
    session, repo = repository_session
    fingerprint = "b" * 64
    record = _base_record(pipeline_fingerprint=fingerprint)
    repo.insert(record)
    session.commit()
    loaded = repo.get_by_logical_identity(fingerprint, SNAPSHOT_CONTRACT_VERSION)
    assert loaded is not None
    assert loaded.pipeline_fingerprint == fingerprint


def test_multiple_null_fingerprint_admission_rejected_allowed(
    repository_session: tuple[Session, SqlAlchemyIntelligenceRunRepository],
) -> None:
    session, repo = repository_session
    first = _base_record(
        run_id=uuid.uuid4(),
        pipeline_fingerprint=None,
        as_of=None,
        outcome="admission_rejected",
        bindings_json=None,
        provenance_json={"pipeline_fingerprint": None},
        stage_presence_json=_stage_presence(dashboard="ABSENT"),
        dashboard_snapshot_json=None,
    )
    second = _base_record(
        run_id=uuid.uuid4(),
        pipeline_fingerprint=None,
        as_of=None,
        outcome="admission_rejected",
        bindings_json=None,
        provenance_json={"pipeline_fingerprint": None},
        stage_presence_json=_stage_presence(dashboard="ABSENT"),
        dashboard_snapshot_json=None,
    )
    repo.insert(first)
    repo.insert(second)
    session.commit()
    assert repo.get_by_run_id(first.run_id) is not None
    assert repo.get_by_run_id(second.run_id) is not None


def test_non_null_duplicate_logical_identity_rejected(
    repository_session: tuple[Session, SqlAlchemyIntelligenceRunRepository],
) -> None:
    session, repo = repository_session
    fingerprint = "c" * 64
    repo.insert(_base_record(pipeline_fingerprint=fingerprint))
    session.commit()
    with pytest.raises(IntelligenceRunIdentityConflictError):
        repo.insert(_base_record(run_id=uuid.uuid4(), pipeline_fingerprint=fingerprint))


def test_versions_and_jsonb_roundtrip(
    repository_session: tuple[Session, SqlAlchemyIntelligenceRunRepository],
) -> None:
    session, repo = repository_session
    record = _base_record(
        human_review_snapshot_json={"decision": "approve", "bounded": True},
        ade_snapshot_json={"outcome": "accept", "bounded": True},
    )
    repo.insert(record)
    session.commit()
    loaded = repo.get_by_run_id(record.run_id)
    assert loaded is not None
    assert loaded.snapshot_contract_version == SNAPSHOT_CONTRACT_VERSION
    assert loaded.persistence_schema_version == PERSISTENCE_SCHEMA_VERSION
    assert loaded.human_review_snapshot_json == {"decision": "approve", "bounded": True}
    assert loaded.ade_snapshot_json == {"outcome": "accept", "bounded": True}
    assert loaded.persisted_at.tzinfo is not None


def test_partial_latest_dashboard_index_exists(engine: Engine) -> None:
    inspector = inspect(engine)
    indexes = inspector.get_indexes("intelligence_runs")
    names = {item["name"] for item in indexes}
    assert "ix_intelligence_runs_latest_dashboard" in names


def test_repository_has_no_update_delete_surface(
    repository_session: tuple[Session, SqlAlchemyIntelligenceRunRepository],
) -> None:
    _, repo = repository_session
    assert not hasattr(repo, "update")
    assert not hasattr(repo, "delete")
    assert not hasattr(repo, "save")
