"""PostgreSQL integration tests for Intelligence Run materializer (WS2)."""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from alembic import command
from alembic.config import Config
from app.intelligence_pipeline import PipelineOutcome, run_intelligence_pipeline
from app.intelligence_runs.constants import SNAPSHOT_CONTRACT_VERSION
from app.intelligence_runs.database import create_session_factory, create_sync_engine, session_scope
from app.intelligence_runs.errors import (
    IntelligenceRunIdentityConflictError,
    IntelligenceRunStorageUnavailableError,
)
from app.intelligence_runs.materializer import IntelligenceRunMaterializer
from app.intelligence_runs.repository import SqlAlchemyIntelligenceRunRepository
from app.intelligence_runs.snapshot import (
    build_authoritative_snapshot,
    canonical_snapshot_json,
)
from sqlalchemy import Engine, text
from sqlalchemy.orm import sessionmaker
from tests.unit.test_intelligence_pipeline_core import VALID_ATTESTATION, _valid_request

pytestmark = pytest.mark.postgres_integration

_API_ROOT = Path(__file__).resolve().parents[2]
PRIVATE_ADE_MARKER = "PRIVATE_ADE_ATTESTATION_PAYLOAD_DO_NOT_PERSIST_INTEGRATION"


def _require_database_url() -> str:
    url = os.environ.get("BERGAMA_DATABASE__URL", "").strip()
    if not url:
        pytest.skip("BERGAMA_DATABASE__URL required for PostgreSQL materializer tests")
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


def test_materialize_completed_dashboard_insert_and_equal_reuse(
    session_factory: sessionmaker,
) -> None:
    materializer = IntelligenceRunMaterializer(session_factory)
    result = run_intelligence_pipeline(_valid_request())
    first = materializer.materialize(result)
    second = materializer.materialize(result)
    assert first.run_id == second.run_id
    assert first.run_id.version == 4
    assert first.pipeline_fingerprint == result.provenance.pipeline_fingerprint
    assert first.dashboard_snapshot_json is not None
    assert first.stage_presence_json["dashboard"] == "PRESENT"


def test_materialize_unequal_duplicate_conflicts(session_factory: sessionmaker) -> None:
    materializer = IntelligenceRunMaterializer(session_factory)
    result = run_intelligence_pipeline(_valid_request())
    materializer.materialize(result)
    snapshot = build_authoritative_snapshot(result)
    fingerprint = snapshot.pipeline_fingerprint
    assert fingerprint is not None
    with session_scope(session_factory) as session:
        repo = SqlAlchemyIntelligenceRunRepository(session)
        existing = repo.get_by_logical_identity(fingerprint, SNAPSHOT_CONTRACT_VERSION)
        assert existing is not None
        existing.provenance_json = {**existing.provenance_json, "tampered": True}
        session.flush()
    with pytest.raises(IntelligenceRunIdentityConflictError):
        materializer.materialize(result)


def test_null_fingerprint_admission_rejected_always_new(
    session_factory: sessionmaker,
) -> None:
    materializer = IntelligenceRunMaterializer(session_factory)
    result = run_intelligence_pipeline(
        _valid_request(hr_requested=True, hr_attestation=None),
    )
    assert result.outcome == PipelineOutcome.ADMISSION_REJECTED
    assert result.provenance.pipeline_fingerprint is None
    first = materializer.materialize(result)
    second = materializer.materialize(result)
    assert first.run_id != second.run_id
    assert first.pipeline_fingerprint is None
    assert second.pipeline_fingerprint is None


def test_ade_private_payload_not_persisted(session_factory: sessionmaker) -> None:
    from app.ai_decision_engine.models import AdeOutcomeKind, AdeProvenance, AdeResult
    from app.ai_decision_engine.policy import (
        ACCEPTANCE_SPECIFICATION_V1,
        DERIVATION_ATTRIBUTION_V1,
        DIGEST_METHOD_V1,
        IDENTITY_SPECIFICATION_V1,
        PROVENANCE_SPECIFICATION_V1,
    )
    from app.ai_decision_engine.policy import (
        POLICY_VERSION_V1 as ADE_POLICY_VERSION_V1,
    )
    from app.ai_decision_engine.reasons import AdeReasonFamily

    def abstain(request: object) -> AdeResult:
        from app.ai_decision_engine.models import AdeEvaluationRequest

        assert isinstance(request, AdeEvaluationRequest)
        assert request.human_review is not None
        return AdeResult(
            outcome_kind=AdeOutcomeKind.EXPLICIT_ABSTENTION,
            policy_version_id=ADE_POLICY_VERSION_V1,
            as_of=request.as_of,
            reason_family=AdeReasonFamily.DETERMINISTIC_ACCEPTANCE_NOT_ESTABLISHED,
            decision_id=None,
            human_review_output_id=request.human_review.human_review_output_id,
            provenance=AdeProvenance(
                policy_version_id=ADE_POLICY_VERSION_V1,
                identity_specification_id=IDENTITY_SPECIFICATION_V1,
                provenance_specification_id=PROVENANCE_SPECIFICATION_V1,
                acceptance_specification_id=ACCEPTANCE_SPECIFICATION_V1,
                digest_method_id=DIGEST_METHOD_V1,
                derivation_attribution_id=DERIVATION_ATTRIBUTION_V1,
                as_of=request.as_of,
                human_review_output_id=request.human_review.human_review_output_id,
                human_review_policy_version_id=request.human_review.policy_version_id,
                human_review_identity_specification_id=(
                    request.human_review.identity_specification_id
                ),
                human_review_provenance_specification_id=(
                    request.human_review.provenance_specification_id
                ),
                human_review_config_fingerprint=(
                    request.human_review.provenance.config_fingerprint
                ),
                human_review_input_fingerprint=request.human_review.provenance.input_fingerprint,
                recorded_attestation_fingerprint=(
                    request.human_review.provenance.recorded_attestation_fingerprint
                ),
                recorded_attestation_payload=PRIVATE_ADE_MARKER,
                config_fingerprint="c" * 64,
                evidence_fingerprint="d" * 64,
            ),
            detail="explicit_abstention_fixture",
        )

    monkey = pytest.MonkeyPatch()
    monkey.setattr("app.intelligence_pipeline.orchestrator.evaluate_ade", abstain)
    try:
        result = run_intelligence_pipeline(
            _valid_request(
                hr_requested=True,
                ade_requested=True,
                hr_attestation=VALID_ATTESTATION,
            )
        )
        materializer = IntelligenceRunMaterializer(session_factory)
        record = materializer.materialize(result)
    finally:
        monkey.undo()

    assert record.ade_snapshot_json is not None
    blob = json.dumps(
        {
            "ade": record.ade_snapshot_json,
            "canonical": canonical_snapshot_json(build_authoritative_snapshot(result)),
            "row": {
                "bindings": record.bindings_json,
                "provenance": record.provenance_json,
                "dashboard": record.dashboard_snapshot_json,
                "hr": record.human_review_snapshot_json,
            },
        }
    )
    assert PRIVATE_ADE_MARKER not in blob
    assert "recorded_attestation_payload" not in blob


def test_lookup_insert_race_equal_reuses(
    session_factory: sessionmaker,
) -> None:
    result = run_intelligence_pipeline(_valid_request())
    materializer = IntelligenceRunMaterializer(session_factory)

    def _run() -> uuid.UUID:
        return materializer.materialize(result).run_id

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(_run)
        second = pool.submit(_run)
        run_ids = {first.result(), second.result()}
    assert len(run_ids) == 1


def test_storage_unavailable_propagates(session_factory: sessionmaker) -> None:
    materializer = IntelligenceRunMaterializer(session_factory)
    result = run_intelligence_pipeline(_valid_request())
    broken_factory = MagicMock()
    broken_factory.side_effect = IntelligenceRunStorageUnavailableError(
        detail="storage unavailable during insert",
    )
    poisoned = IntelligenceRunMaterializer(broken_factory)  # type: ignore[arg-type]
    with pytest.raises(IntelligenceRunStorageUnavailableError):
        poisoned.materialize(result)
    record = materializer.materialize(result)
    assert record.run_id.version == 4


def test_repository_remains_insert_only_after_materialize(
    session_factory: sessionmaker,
) -> None:
    materializer = IntelligenceRunMaterializer(session_factory)
    result = run_intelligence_pipeline(_valid_request())
    materializer.materialize(result)
    with session_scope(session_factory) as session:
        repo = SqlAlchemyIntelligenceRunRepository(session)
        assert not hasattr(repo, "update")
        assert not hasattr(repo, "delete")
        assert not hasattr(repo, "upsert")
