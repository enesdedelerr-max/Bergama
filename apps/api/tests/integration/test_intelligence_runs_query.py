"""PostgreSQL integration tests for Intelligence Run query / latest dashboard (WS3)."""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.core.clock import FixedClock
from app.intelligence_pipeline import run_intelligence_pipeline
from app.intelligence_runs.constants import SNAPSHOT_CONTRACT_VERSION
from app.intelligence_runs.database import create_session_factory, create_sync_engine, session_scope
from app.intelligence_runs.materializer import IntelligenceRunMaterializer
from app.intelligence_runs.query_service import IntelligenceRunQueryService
from app.intelligence_runs.repository import SqlAlchemyIntelligenceRunRepository
from sqlalchemy import Engine, text
from sqlalchemy.orm import sessionmaker
from tests.unit.test_intelligence_pipeline_core import VALID_ATTESTATION, _valid_request

pytestmark = pytest.mark.postgres_integration

_API_ROOT = Path(__file__).resolve().parents[2]
FIXED_NOW = datetime(2026, 10, 7, 20, 0, tzinfo=UTC)


def _require_database_url() -> str:
    url = os.environ.get("BERGAMA_DATABASE__URL", "").strip()
    if not url:
        pytest.skip("BERGAMA_DATABASE__URL required for PostgreSQL query tests")
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


def _materialize(session_factory: sessionmaker, **kwargs: object) -> uuid.UUID:
    materializer = IntelligenceRunMaterializer(session_factory)
    result = run_intelligence_pipeline(_valid_request(**kwargs))  # type: ignore[arg-type]
    return materializer.materialize(result).run_id


def _stamp_ordering(
    session_factory: sessionmaker,
    *,
    run_id: uuid.UUID,
    hours_ago: int,
) -> None:
    with session_scope(session_factory) as session:
        session.execute(
            text(
                "UPDATE intelligence_runs SET as_of = :as_of, persisted_at = :persisted "
                "WHERE run_id = :run_id"
            ),
            {
                "as_of": FIXED_NOW - timedelta(hours=hours_ago),
                "persisted": FIXED_NOW - timedelta(hours=hours_ago),
                "run_id": run_id,
            },
        )
        session.commit()


def _assert_latest_fail_closed_no_skip(
    session_factory: sessionmaker,
    *,
    expected_code: str,
    expected_candidate_id: uuid.UUID,
) -> None:
    with session_scope(session_factory) as session:
        query = IntelligenceRunQueryService(session=session, clock=FixedClock(FIXED_NOW))
        with pytest.raises(Exception) as exc:
            query.get_latest_dashboard_capable()
        assert exc.value.code == expected_code  # type: ignore[attr-defined]
        repo = SqlAlchemyIntelligenceRunRepository(session)
        candidate = repo.get_latest_dashboard_storage_candidate()
        assert candidate is not None
        assert candidate.run_id == expected_candidate_id


def test_real_run_and_fingerprint_lookup(session_factory: sessionmaker) -> None:
    run_id = _materialize(session_factory)
    with session_scope(session_factory) as session:
        query = IntelligenceRunQueryService(session=session, clock=FixedClock(FIXED_NOW))
        by_id = query.get_run_by_id(str(run_id))
        assert by_id.run_id == str(run_id)
        assert by_id.pipeline_fingerprint is not None
        by_fp = query.get_run_by_fingerprint(by_id.pipeline_fingerprint)
        assert by_fp.run_id == str(run_id)
        assert by_fp.snapshot_contract_version == SNAPSHOT_CONTRACT_VERSION


def test_latest_dashboard_ordering_and_eligibility(session_factory: sessionmaker) -> None:
    older_id = _materialize(session_factory)
    newer_id = _materialize(session_factory)
    # Force distinct as_of / persisted_at for deterministic ordering.
    with session_scope(session_factory) as session:
        session.execute(
            text(
                "UPDATE intelligence_runs SET as_of = :as_of, persisted_at = :persisted "
                "WHERE run_id = :run_id"
            ),
            {
                "as_of": FIXED_NOW - timedelta(hours=2),
                "persisted": FIXED_NOW - timedelta(hours=2),
                "run_id": older_id,
            },
        )
        session.execute(
            text(
                "UPDATE intelligence_runs SET as_of = :as_of, persisted_at = :persisted "
                "WHERE run_id = :run_id"
            ),
            {
                "as_of": FIXED_NOW - timedelta(hours=1),
                "persisted": FIXED_NOW - timedelta(hours=1),
                "run_id": newer_id,
            },
        )
        session.commit()

    with session_scope(session_factory) as session:
        query = IntelligenceRunQueryService(session=session, clock=FixedClock(FIXED_NOW))
        latest = query.get_latest_dashboard_capable()
        assert latest.run_id == str(newer_id)
        assert latest.stage_presence["dashboard"] == "PRESENT"
        assert latest.dashboard is not None


def test_null_as_of_admission_rejected_not_dashboard_capable(
    session_factory: sessionmaker,
) -> None:
    materializer = IntelligenceRunMaterializer(session_factory)
    rejected = run_intelligence_pipeline(_valid_request(hr_requested=True, hr_attestation=None))
    materializer.materialize(rejected)
    with session_scope(session_factory) as session:
        query = IntelligenceRunQueryService(session=session, clock=FixedClock(FIXED_NOW))
        with pytest.raises(Exception) as exc:
            query.get_latest_dashboard_capable()
        assert exc.value.code == "intelligence.runs.run_not_found"  # type: ignore[attr-defined]


def test_newest_corrupt_object_fail_closed_no_skip(session_factory: sessionmaker) -> None:
    good_id = _materialize(session_factory)
    bad_id = _materialize(session_factory)
    _stamp_ordering(session_factory, run_id=good_id, hours_ago=3)
    with session_scope(session_factory) as session:
        session.execute(
            text(
                "UPDATE intelligence_runs SET as_of = :as_of, persisted_at = :persisted, "
                "dashboard_snapshot_json = CAST(:payload AS jsonb) "
                "WHERE run_id = :run_id"
            ),
            {
                "as_of": FIXED_NOW - timedelta(hours=1),
                "persisted": FIXED_NOW - timedelta(hours=1),
                "payload": json.dumps({"corrupt": True}),
                "run_id": bad_id,
            },
        )
        session.commit()
    _assert_latest_fail_closed_no_skip(
        session_factory,
        expected_code="intelligence.runs.corrupt_persisted_snapshot",
        expected_candidate_id=bad_id,
    )


def test_newest_present_sql_null_dashboard_fail_closed_no_skip(
    session_factory: sessionmaker,
) -> None:
    good_id = _materialize(session_factory)
    bad_id = _materialize(session_factory)
    _stamp_ordering(session_factory, run_id=good_id, hours_ago=3)
    with session_scope(session_factory) as session:
        session.execute(
            text(
                "UPDATE intelligence_runs SET as_of = :as_of, persisted_at = :persisted, "
                "dashboard_snapshot_json = NULL WHERE run_id = :run_id"
            ),
            {
                "as_of": FIXED_NOW - timedelta(hours=1),
                "persisted": FIXED_NOW - timedelta(hours=1),
                "run_id": bad_id,
            },
        )
        session.commit()
    _assert_latest_fail_closed_no_skip(
        session_factory,
        expected_code="intelligence.runs.corrupt_persisted_snapshot",
        expected_candidate_id=bad_id,
    )


def test_newest_present_json_null_dashboard_fail_closed_no_skip(
    session_factory: sessionmaker,
) -> None:
    good_id = _materialize(session_factory)
    bad_id = _materialize(session_factory)
    _stamp_ordering(session_factory, run_id=good_id, hours_ago=3)
    with session_scope(session_factory) as session:
        session.execute(
            text(
                "UPDATE intelligence_runs SET as_of = :as_of, persisted_at = :persisted, "
                "dashboard_snapshot_json = 'null'::jsonb WHERE run_id = :run_id"
            ),
            {
                "as_of": FIXED_NOW - timedelta(hours=1),
                "persisted": FIXED_NOW - timedelta(hours=1),
                "run_id": bad_id,
            },
        )
        session.commit()
    _assert_latest_fail_closed_no_skip(
        session_factory,
        expected_code="intelligence.runs.corrupt_persisted_snapshot",
        expected_candidate_id=bad_id,
    )


def test_newest_present_non_object_dashboard_fail_closed_no_skip(
    session_factory: sessionmaker,
) -> None:
    good_id = _materialize(session_factory)
    bad_id = _materialize(session_factory)
    _stamp_ordering(session_factory, run_id=good_id, hours_ago=3)
    with session_scope(session_factory) as session:
        session.execute(
            text(
                "UPDATE intelligence_runs SET as_of = :as_of, persisted_at = :persisted, "
                "dashboard_snapshot_json = CAST(:payload AS jsonb) "
                "WHERE run_id = :run_id"
            ),
            {
                "as_of": FIXED_NOW - timedelta(hours=1),
                "persisted": FIXED_NOW - timedelta(hours=1),
                "payload": json.dumps(["not", "an", "object"]),
                "run_id": bad_id,
            },
        )
        session.commit()
    _assert_latest_fail_closed_no_skip(
        session_factory,
        expected_code="intelligence.runs.corrupt_persisted_snapshot",
        expected_candidate_id=bad_id,
    )


def test_newest_unsupported_candidate_fail_closed_no_skip(
    engine: Engine,
    session_factory: sessionmaker,
) -> None:
    from sqlalchemy.orm import Session

    good_id = _materialize(session_factory)
    bad_id = _materialize(session_factory)
    # Temporarily relax the version CHECK inside a rolled-back transaction so the
    # shared schema remains intact for other tests.
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            conn.execute(
                text(
                    "ALTER TABLE intelligence_runs DROP CONSTRAINT "
                    "ck_intelligence_runs_snapshot_contract_version"
                )
            )
            conn.execute(
                text(
                    "UPDATE intelligence_runs SET as_of = :as_of, persisted_at = :persisted "
                    "WHERE run_id = :run_id"
                ),
                {
                    "as_of": FIXED_NOW - timedelta(hours=5),
                    "persisted": FIXED_NOW - timedelta(hours=5),
                    "run_id": good_id,
                },
            )
            conn.execute(
                text(
                    "UPDATE intelligence_runs SET as_of = :as_of, persisted_at = :persisted, "
                    "snapshot_contract_version = :version WHERE run_id = :run_id"
                ),
                {
                    "as_of": FIXED_NOW - timedelta(hours=1),
                    "persisted": FIXED_NOW - timedelta(hours=1),
                    "version": "intelligence-run-productization.snapshot.v0",
                    "run_id": bad_id,
                },
            )
            session = Session(bind=conn)
            try:
                query = IntelligenceRunQueryService(session=session, clock=FixedClock(FIXED_NOW))
                with pytest.raises(Exception) as exc:
                    query.get_latest_dashboard_capable()
                assert (
                    exc.value.code  # type: ignore[attr-defined]
                    == "intelligence.runs.unsupported_snapshot_contract"
                )
                repo = SqlAlchemyIntelligenceRunRepository(session)
                candidate = repo.get_latest_dashboard_storage_candidate()
                assert candidate is not None
                assert candidate.run_id == bad_id
            finally:
                session.close()
        finally:
            trans.rollback()


def test_latest_run_id_asc_tie_break(session_factory: sessionmaker) -> None:
    first_id = _materialize(session_factory)
    second_id = _materialize(session_factory)
    tie_as_of = FIXED_NOW - timedelta(hours=1)
    tie_persisted = FIXED_NOW - timedelta(minutes=30)
    with session_scope(session_factory) as session:
        for run_id in (first_id, second_id):
            session.execute(
                text(
                    "UPDATE intelligence_runs SET as_of = :as_of, persisted_at = :persisted "
                    "WHERE run_id = :run_id"
                ),
                {"as_of": tie_as_of, "persisted": tie_persisted, "run_id": run_id},
            )
        session.commit()
    expected_winner = min(first_id, second_id)
    with session_scope(session_factory) as session:
        query = IntelligenceRunQueryService(session=session, clock=FixedClock(FIXED_NOW))
        latest = query.get_latest_dashboard_capable()
        assert latest.run_id == str(expected_winner)


def test_stage_subresources_real(session_factory: sessionmaker) -> None:
    run_id = _materialize(
        session_factory,
        hr_requested=True,
        ade_requested=True,
        hr_attestation=VALID_ATTESTATION,
    )
    with session_scope(session_factory) as session:
        query = IntelligenceRunQueryService(session=session, clock=FixedClock(FIXED_NOW))
        dash = query.get_dashboard(str(run_id))
        hr = query.get_human_review(str(run_id))
        ade = query.get_ade(str(run_id))
        assert dash.dashboard is not None
        assert hr.human_review is not None
        assert ade.ade is not None
        assert "recorded_attestation_payload" not in ade.model_dump_json()
