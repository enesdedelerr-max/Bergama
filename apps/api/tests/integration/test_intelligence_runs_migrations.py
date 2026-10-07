"""PostgreSQL migration upgrade / downgrade / re-upgrade tests (WS1)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.intelligence_runs.database import create_sync_engine
from sqlalchemy import Engine, inspect, text

pytestmark = pytest.mark.postgres_integration

_API_ROOT = Path(__file__).resolve().parents[2]
_EXPECTED_COLUMNS = {
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
}


def _require_database_url() -> str:
    url = os.environ.get("BERGAMA_DATABASE__URL", "").strip()
    if not url:
        pytest.skip("BERGAMA_DATABASE__URL required for PostgreSQL migration tests")
    return url


def _alembic_config(url: str) -> Config:
    cfg = Config(str(_API_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_API_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    os.environ["BERGAMA_DATABASE__URL"] = url
    return cfg


def _reset_schema(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS intelligence_runs CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))


@pytest.fixture
def engine() -> Iterator[Engine]:
    url = _require_database_url()
    eng = create_sync_engine(url)
    _reset_schema(eng)
    yield eng
    _reset_schema(eng)
    eng.dispose()


def _assert_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    assert "intelligence_runs" in inspector.get_table_names()
    columns = {col["name"] for col in inspector.get_columns("intelligence_runs")}
    assert columns >= _EXPECTED_COLUMNS
    pk = inspector.get_pk_constraint("intelligence_runs")
    assert pk["constrained_columns"] == ["run_id"]
    unique = inspector.get_unique_constraints("intelligence_runs")
    unique_names = {item["name"] for item in unique}
    assert "uq_intelligence_runs_fingerprint_snapshot_version" in unique_names
    indexes = inspector.get_indexes("intelligence_runs")
    index_names = {item["name"] for item in indexes}
    assert "ix_intelligence_runs_latest_dashboard" in index_names
    with engine.connect() as connection:
        check_rows = connection.execute(
            text(
                """
                SELECT conname
                FROM pg_constraint
                WHERE conrelid = 'intelligence_runs'::regclass
                  AND contype = 'c'
                """
            )
        ).fetchall()
    check_names = {row[0] for row in check_rows}
    assert "ck_intelligence_runs_outcome" in check_names
    assert "ck_intelligence_runs_pipeline_fingerprint" in check_names
    assert "ck_intelligence_runs_failure_detail_length" in check_names
    assert "ck_intelligence_runs_snapshot_contract_version" in check_names
    assert "ck_intelligence_runs_persistence_schema_version" in check_names


def test_upgrade_downgrade_reupgrade(engine: Engine) -> None:
    url = _require_database_url()
    cfg = _alembic_config(url)

    command.upgrade(cfg, "head")
    _assert_schema(engine)

    command.downgrade(cfg, "base")
    inspector = inspect(engine)
    assert "intelligence_runs" not in inspector.get_table_names()

    command.upgrade(cfg, "head")
    _assert_schema(engine)
