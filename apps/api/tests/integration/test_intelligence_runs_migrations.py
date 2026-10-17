"""PostgreSQL migration upgrade / downgrade / re-upgrade tests (WS1/WS2)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.intelligence_runs.constants import (
    PERSISTENCE_SCHEMA_VERSION_V1,
    PERSISTENCE_SCHEMA_VERSION_V2,
    SNAPSHOT_CONTRACT_VERSION_V1,
    SNAPSHOT_CONTRACT_VERSION_V2,
)
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
    "analyst_snapshot_json",
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


def _check_defs(engine: Engine) -> dict[str, str]:
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT conname, pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid = 'intelligence_runs'::regclass
                  AND contype = 'c'
                """
            )
        ).fetchall()
    return {row[0]: row[1] for row in rows}


def _assert_head_schema(engine: Engine) -> None:
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
    check_names = set(_check_defs(engine))
    assert "ck_intelligence_runs_outcome" in check_names
    assert "ck_intelligence_runs_pipeline_fingerprint" in check_names
    assert "ck_intelligence_runs_failure_detail_length" in check_names
    assert "ck_intelligence_runs_snapshot_contract_version" in check_names
    assert "ck_intelligence_runs_persistence_schema_version" in check_names
    assert "ck_intelligence_runs_analyst_snapshot_version_outcome" in check_names
    defs = _check_defs(engine)
    assert SNAPSHOT_CONTRACT_VERSION_V1 in defs["ck_intelligence_runs_snapshot_contract_version"]
    assert SNAPSHOT_CONTRACT_VERSION_V2 in defs["ck_intelligence_runs_snapshot_contract_version"]
    assert PERSISTENCE_SCHEMA_VERSION_V1 in defs["ck_intelligence_runs_persistence_schema_version"]
    assert PERSISTENCE_SCHEMA_VERSION_V2 in defs["ck_intelligence_runs_persistence_schema_version"]


def test_fresh_upgrade_to_0001_creates_v1_only_checks(engine: Engine) -> None:
    url = _require_database_url()
    cfg = _alembic_config(url)
    command.upgrade(cfg, "20261007_0001")

    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("intelligence_runs")}
    assert "analyst_snapshot_json" not in columns
    defs = _check_defs(engine)
    snap = defs["ck_intelligence_runs_snapshot_contract_version"]
    pers = defs["ck_intelligence_runs_persistence_schema_version"]
    assert SNAPSHOT_CONTRACT_VERSION_V1 in snap
    assert SNAPSHOT_CONTRACT_VERSION_V2 not in snap
    assert PERSISTENCE_SCHEMA_VERSION_V1 in pers
    assert PERSISTENCE_SCHEMA_VERSION_V2 not in pers
    assert "=" in snap
    assert "IN (" not in snap.upper().replace(" ", "")


def test_upgrade_downgrade_reupgrade(engine: Engine) -> None:
    url = _require_database_url()
    cfg = _alembic_config(url)

    command.upgrade(cfg, "head")
    _assert_head_schema(engine)

    command.downgrade(cfg, "base")
    inspector = inspect(engine)
    assert "intelligence_runs" not in inspector.get_table_names()

    command.upgrade(cfg, "head")
    _assert_head_schema(engine)


def test_existing_v1_db_upgrade_preserves_historical_row(engine: Engine) -> None:
    url = _require_database_url()
    cfg = _alembic_config(url)
    command.upgrade(cfg, "20261007_0001")

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO intelligence_runs (
                    run_id,
                    pipeline_fingerprint,
                    as_of,
                    outcome,
                    provenance_json,
                    stage_presence_json,
                    dashboard_snapshot_json,
                    snapshot_contract_version,
                    persistence_schema_version,
                    persisted_at
                ) VALUES (
                    gen_random_uuid(),
                    :fp,
                    TIMESTAMPTZ '2026-10-07 12:00:00+00',
                    'completed_dashboard',
                    CAST(:prov AS jsonb),
                    CAST(:presence AS jsonb),
                    CAST(:dash AS jsonb),
                    :snap_v1,
                    :pers_v1,
                    TIMESTAMPTZ '2026-10-07 12:05:00+00'
                )
                """
            ),
            {
                "fp": "c" * 64,
                "prov": '{"pipeline_fingerprint":"' + ("c" * 64) + '"}',
                "presence": (
                    '{"watchlist":"PRESENT","gap":"PRESENT","catalyst":"PRESENT",'
                    '"score":"PRESENT","briefing":"PRESENT","dashboard":"PRESENT",'
                    '"human_review":"ABSENT","ade":"ABSENT"}'
                ),
                "dash": '{"kind":"dashboard","immutable":true}',
                "snap_v1": SNAPSHOT_CONTRACT_VERSION_V1,
                "pers_v1": PERSISTENCE_SCHEMA_VERSION_V1,
            },
        )

    with engine.connect() as connection:
        before = connection.execute(
            text(
                "SELECT pipeline_fingerprint, outcome, dashboard_snapshot_json, "
                "snapshot_contract_version, persistence_schema_version "
                "FROM intelligence_runs WHERE pipeline_fingerprint = :fp"
            ),
            {"fp": "c" * 64},
        ).one()

    command.upgrade(cfg, "head")
    _assert_head_schema(engine)

    with engine.connect() as connection:
        after = connection.execute(
            text(
                "SELECT pipeline_fingerprint, outcome, dashboard_snapshot_json, "
                "snapshot_contract_version, persistence_schema_version, "
                "analyst_snapshot_json "
                "FROM intelligence_runs WHERE pipeline_fingerprint = :fp"
            ),
            {"fp": "c" * 64},
        ).one()
    assert after[0] == before[0]
    assert after[1] == before[1]
    assert after[2] == before[2]
    assert after[3] == before[3] == SNAPSHOT_CONTRACT_VERSION_V1
    assert after[4] == before[4] == PERSISTENCE_SCHEMA_VERSION_V1
    assert after[5] is None


def test_expand_preserves_v1_row_and_blocks_unsafe_downgrade(engine: Engine) -> None:
    url = _require_database_url()
    cfg = _alembic_config(url)
    command.upgrade(cfg, "head")

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO intelligence_runs (
                    run_id,
                    pipeline_fingerprint,
                    as_of,
                    outcome,
                    provenance_json,
                    stage_presence_json,
                    dashboard_snapshot_json,
                    analyst_snapshot_json,
                    snapshot_contract_version,
                    persistence_schema_version,
                    persisted_at
                ) VALUES (
                    gen_random_uuid(),
                    :fp,
                    TIMESTAMPTZ '2026-10-07 12:00:00+00',
                    'completed_dashboard',
                    CAST(:prov AS jsonb),
                    CAST(:presence AS jsonb),
                    CAST(:dash AS jsonb),
                    NULL,
                    :snap_v1,
                    :pers_v1,
                    TIMESTAMPTZ '2026-10-07 12:05:00+00'
                )
                """
            ),
            {
                "fp": "a" * 64,
                "prov": '{"pipeline_fingerprint":"' + ("a" * 64) + '"}',
                "presence": (
                    '{"watchlist":"PRESENT","gap":"PRESENT","catalyst":"PRESENT",'
                    '"score":"PRESENT","briefing":"PRESENT","dashboard":"PRESENT",'
                    '"human_review":"ABSENT","ade":"ABSENT"}'
                ),
                "dash": '{"kind":"dashboard"}',
                "snap_v1": SNAPSHOT_CONTRACT_VERSION_V1,
                "pers_v1": PERSISTENCE_SCHEMA_VERSION_V1,
            },
        )

    with engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT analyst_snapshot_json, snapshot_contract_version "
                "FROM intelligence_runs WHERE pipeline_fingerprint = :fp"
            ),
            {"fp": "a" * 64},
        ).one()
    assert row[0] is None
    assert row[1] == SNAPSHOT_CONTRACT_VERSION_V1

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO intelligence_runs (
                    run_id,
                    pipeline_fingerprint,
                    as_of,
                    outcome,
                    provenance_json,
                    stage_presence_json,
                    dashboard_snapshot_json,
                    analyst_snapshot_json,
                    snapshot_contract_version,
                    persistence_schema_version,
                    persisted_at
                ) VALUES (
                    gen_random_uuid(),
                    :fp,
                    TIMESTAMPTZ '2026-10-07 13:00:00+00',
                    'completed_dashboard',
                    CAST(:prov AS jsonb),
                    CAST(:presence AS jsonb),
                    CAST(:dash AS jsonb),
                    CAST(:analyst AS jsonb),
                    :snap_v2,
                    :pers_v2,
                    TIMESTAMPTZ '2026-10-07 13:05:00+00'
                )
                """
            ),
            {
                "fp": "b" * 64,
                "prov": '{"pipeline_fingerprint":"' + ("b" * 64) + '"}',
                "presence": (
                    '{"watchlist":"PRESENT","gap":"PRESENT","catalyst":"PRESENT",'
                    '"score":"PRESENT","briefing":"PRESENT","dashboard":"PRESENT",'
                    '"human_review":"ABSENT","ade":"ABSENT"}'
                ),
                "dash": '{"kind":"dashboard"}',
                "analyst": '{"evaluation_state":"INSUFFICIENT_EVIDENCE"}',
                "snap_v2": SNAPSHOT_CONTRACT_VERSION_V2,
                "pers_v2": PERSISTENCE_SCHEMA_VERSION_V2,
            },
        )

    with pytest.raises(RuntimeError, match="cannot downgrade intelligence_runs analyst expand"):
        command.downgrade(cfg, "20261007_0001")

    with engine.begin() as connection:
        connection.execute(
            text(
                "DELETE FROM intelligence_runs "
                "WHERE snapshot_contract_version = :v2 OR analyst_snapshot_json IS NOT NULL"
            ),
            {"v2": SNAPSHOT_CONTRACT_VERSION_V2},
        )

    command.downgrade(cfg, "20261007_0001")
    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("intelligence_runs")}
    assert "analyst_snapshot_json" not in columns

    with engine.connect() as connection:
        remaining = connection.execute(text("SELECT COUNT(*) FROM intelligence_runs")).scalar_one()
    assert remaining == 1
