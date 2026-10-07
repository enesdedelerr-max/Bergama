"""Unit tests for Intelligence Run authoritative snapshot / equality (WS2)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
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
from app.human_review.models import HumanReviewRecordedAttestation
from app.intelligence_pipeline import PipelineOutcome, run_intelligence_pipeline
from app.intelligence_pipeline.models import PipelineProvenance, PipelineResult
from app.intelligence_runs.constants import (
    FAILURE_DETAIL_MAX_CHARS,
    PERSISTENCE_SCHEMA_VERSION,
    SNAPSHOT_CONTRACT_VERSION,
)
from app.intelligence_runs.errors import IntelligenceRunInvalidMaterializationError
from app.intelligence_runs.models import IntelligenceRunRecord
from app.intelligence_runs.snapshot import (
    STAGE_KEYS,
    STAGE_STATUSES,
    StagePresenceStatus,
    build_ade_product_snapshot,
    build_authoritative_snapshot,
    build_stage_presence,
    canonical_snapshot_json,
    canonical_snapshots_equal,
    enforce_dashboard_invariant,
    reconstruct_authoritative_snapshot,
)
from tests.unit.test_intelligence_pipeline_core import VALID_ATTESTATION, _valid_request

PRIVATE_ADE_MARKER = "PRIVATE_ADE_ATTESTATION_PAYLOAD_DO_NOT_PERSIST"


def test_frozen_versions_and_stage_contract() -> None:
    assert SNAPSHOT_CONTRACT_VERSION == "intelligence-run-productization.snapshot.v1"
    assert PERSISTENCE_SCHEMA_VERSION == "intelligence-run-productization.persistence.v1"
    assert len(STAGE_KEYS) == 8
    assert STAGE_KEYS == (
        "watchlist",
        "gap",
        "catalyst",
        "score",
        "briefing",
        "dashboard",
        "human_review",
        "ade",
    )
    assert set(STAGE_STATUSES) == {
        "NOT_EXECUTED",
        "ABSENT",
        "EMPTY",
        "FAILED",
        "PRESENT",
        "ABSTAINED",
    }


def test_completed_dashboard_snapshot_and_stage_presence() -> None:
    result = run_intelligence_pipeline(_valid_request())
    snapshot = build_authoritative_snapshot(result)
    assert snapshot.outcome == "completed_dashboard"
    assert snapshot.snapshot_contract_version == SNAPSHOT_CONTRACT_VERSION
    assert snapshot.pipeline_fingerprint is not None
    assert snapshot.bindings is not None
    assert snapshot.dashboard_snapshot is not None
    assert snapshot.human_review_snapshot is None
    assert snapshot.ade_snapshot is None
    presence = snapshot.stage_presence
    assert tuple(presence.keys()) == STAGE_KEYS
    assert presence["dashboard"] == StagePresenceStatus.PRESENT.value
    assert presence["human_review"] == StagePresenceStatus.ABSENT.value
    assert presence["ade"] == StagePresenceStatus.ABSENT.value
    enforce_dashboard_invariant(snapshot)


def test_admission_rejected_null_identity() -> None:
    result = run_intelligence_pipeline(
        _valid_request(hr_requested=True, hr_attestation=None),
    )
    assert result.outcome == PipelineOutcome.ADMISSION_REJECTED
    snapshot = build_authoritative_snapshot(result)
    assert snapshot.pipeline_fingerprint is None
    assert snapshot.as_of is None
    assert snapshot.bindings is None
    assert snapshot.dashboard_snapshot is None
    assert all(
        snapshot.stage_presence[key] == StagePresenceStatus.NOT_EXECUTED.value
        for key in ("watchlist", "gap", "catalyst", "score", "briefing")
    )
    assert snapshot.stage_presence["dashboard"] == StagePresenceStatus.ABSENT.value


def test_required_stage_failed_snapshot() -> None:
    monkey = pytest.MonkeyPatch()
    monkey.setattr(
        "app.intelligence_pipeline.orchestrator.scan_gaps",
        MagicMock(side_effect=ValueError("gap_fail")),
    )
    try:
        result = run_intelligence_pipeline(_valid_request())
        snapshot = build_authoritative_snapshot(result)
    finally:
        monkey.undo()
    assert snapshot.outcome == "required_stage_failed"
    assert snapshot.failed_stage == "gap"
    assert snapshot.failure_detail is not None
    assert len(snapshot.failure_detail) <= FAILURE_DETAIL_MAX_CHARS
    assert snapshot.stage_presence["gap"] == StagePresenceStatus.FAILED.value
    assert snapshot.stage_presence["catalyst"] == StagePresenceStatus.NOT_EXECUTED.value


def test_completed_human_review_and_ade_accept() -> None:
    result = run_intelligence_pipeline(
        _valid_request(
            hr_requested=True,
            ade_requested=True,
            hr_attestation=VALID_ATTESTATION,
        )
    )
    assert result.outcome == PipelineOutcome.COMPLETED_ADE_ACCEPT
    snapshot = build_authoritative_snapshot(result)
    assert snapshot.human_review_snapshot is not None
    assert snapshot.ade_snapshot is not None
    assert snapshot.stage_presence["human_review"] == StagePresenceStatus.PRESENT.value
    assert snapshot.stage_presence["ade"] == StagePresenceStatus.PRESENT.value
    assert "recorded_attestation_payload" not in json.dumps(snapshot.ade_snapshot)


def test_completed_ade_abstain_stage_presence(monkeypatch: pytest.MonkeyPatch) -> None:
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

    monkeypatch.setattr("app.intelligence_pipeline.orchestrator.evaluate_ade", abstain)
    result = run_intelligence_pipeline(
        _valid_request(
            hr_requested=True,
            ade_requested=True,
            hr_attestation=VALID_ATTESTATION,
        )
    )
    assert result.outcome == PipelineOutcome.COMPLETED_ADE_ABSTAIN
    assert result.ade is not None
    assert result.ade.provenance.recorded_attestation_payload == PRIVATE_ADE_MARKER
    snapshot = build_authoritative_snapshot(result)
    assert snapshot.stage_presence["ade"] == StagePresenceStatus.ABSTAINED.value
    serialized = canonical_snapshot_json(snapshot)
    assert PRIVATE_ADE_MARKER not in serialized
    assert "recorded_attestation_payload" not in serialized
    assert PRIVATE_ADE_MARKER not in json.dumps(snapshot.ade_snapshot)


def test_ade_product_snapshot_excludes_private_payload() -> None:
    ade = AdeResult(
        outcome_kind=AdeOutcomeKind.AUTHORITATIVE_DECISION,
        policy_version_id=ADE_POLICY_VERSION_V1,
        as_of=datetime(2026, 10, 7, 12, 0, tzinfo=UTC),
        reason_family=AdeReasonFamily.ACCEPTED_GOVERNED_EVIDENCE,
        decision_id="a" * 64,
        human_review_output_id="b" * 64,
        provenance=AdeProvenance(
            policy_version_id=ADE_POLICY_VERSION_V1,
            identity_specification_id=IDENTITY_SPECIFICATION_V1,
            provenance_specification_id=PROVENANCE_SPECIFICATION_V1,
            acceptance_specification_id=ACCEPTANCE_SPECIFICATION_V1,
            digest_method_id=DIGEST_METHOD_V1,
            derivation_attribution_id=DERIVATION_ATTRIBUTION_V1,
            as_of=datetime(2026, 10, 7, 12, 0, tzinfo=UTC),
            human_review_output_id="b" * 64,
            recorded_attestation_fingerprint="e" * 64,
            recorded_attestation_payload=PRIVATE_ADE_MARKER,
            config_fingerprint="c" * 64,
            evidence_fingerprint="d" * 64,
        ),
        detail="ok",
    )
    product = build_ade_product_snapshot(ade)
    assert "recorded_attestation_payload" not in product["provenance"]
    assert PRIVATE_ADE_MARKER not in json.dumps(product)


def test_dashboard_invariant_rejects_mismatches() -> None:
    result = run_intelligence_pipeline(_valid_request())
    snapshot = build_authoritative_snapshot(result)
    broken = snapshot.model_copy(update={"dashboard_snapshot": None})
    with pytest.raises(IntelligenceRunInvalidMaterializationError):
        enforce_dashboard_invariant(broken)
    absent = snapshot.model_copy(
        update={
            "stage_presence": {
                **snapshot.stage_presence,
                "dashboard": StagePresenceStatus.ABSENT.value,
            }
        }
    )
    with pytest.raises(IntelligenceRunInvalidMaterializationError):
        enforce_dashboard_invariant(absent)


def test_canonical_equality_deterministic_and_exclusions() -> None:
    result = run_intelligence_pipeline(_valid_request())
    left = build_authoritative_snapshot(result)
    right = build_authoritative_snapshot(result)
    assert canonical_snapshots_equal(left, right)
    payload = left.model_dump(mode="json")
    reordered = {key: payload[key] for key in sorted(payload.keys(), reverse=True)}
    assert json.dumps(reordered, sort_keys=True, separators=(",", ":"), ensure_ascii=False) == (
        canonical_snapshot_json(left)
    )
    text = canonical_snapshot_json(left)
    assert "run_id" not in text
    assert "persisted_at" not in text
    assert "age_seconds" not in text
    assert "persistence_schema_version" not in text
    assert "snapshot_contract_version" in text


def test_reconstruct_excludes_storage_metadata() -> None:
    result = run_intelligence_pipeline(_valid_request())
    snapshot = build_authoritative_snapshot(result)
    record = IntelligenceRunRecord(
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
        persisted_at=datetime(2026, 10, 7, 15, 0, tzinfo=UTC),
    )
    reconstructed = reconstruct_authoritative_snapshot(record)
    assert canonical_snapshots_equal(snapshot, reconstructed)
    assert record.run_id.version == 4
    assert record.persisted_at is not None


def test_invalid_completed_dashboard_without_dashboard_rejected() -> None:
    result = run_intelligence_pipeline(_valid_request())
    broken = PipelineResult(
        outcome=PipelineOutcome.COMPLETED_DASHBOARD,
        as_of=result.as_of,
        bindings=result.bindings,
        provenance=result.provenance,
        watchlist=result.watchlist,
        gaps=result.gaps,
        catalysts=result.catalysts,
        scores=result.scores,
        briefing=result.briefing,
        dashboard=None,
    )
    with pytest.raises(IntelligenceRunInvalidMaterializationError):
        build_authoritative_snapshot(broken)


def test_stage_presence_helper_matches_snapshot() -> None:
    result = run_intelligence_pipeline(_valid_request())
    assert build_stage_presence(result) == build_authoritative_snapshot(result).stage_presence


def test_failure_detail_bound_enforced() -> None:
    result = run_intelligence_pipeline(_valid_request())
    oversized = "x" * (FAILURE_DETAIL_MAX_CHARS + 50)
    broken = PipelineResult(
        outcome=PipelineOutcome.REQUIRED_STAGE_FAILED,
        as_of=result.as_of,
        bindings=result.bindings,
        provenance=PipelineProvenance(
            as_of=result.as_of,
            stage_order=result.provenance.stage_order,
            executed_stages=("watchlist", "gap"),
            pipeline_fingerprint=result.provenance.pipeline_fingerprint,
            outcome=PipelineOutcome.REQUIRED_STAGE_FAILED,
            failed_stage="gap",
        ),
        watchlist=result.watchlist,
        gaps=None,
        failed_stage="gap",
        failure_error_type="ValueError",
        failure_detail=oversized,
    )
    snapshot = build_authoritative_snapshot(broken)
    assert snapshot.failure_detail is not None
    assert len(snapshot.failure_detail) <= FAILURE_DETAIL_MAX_CHARS


def test_hr_attestation_type_available() -> None:
    # Sanity: public HR attestation contract remains importable for fixtures.
    assert isinstance(VALID_ATTESTATION, HumanReviewRecordedAttestation)
    assert VALID_ATTESTATION.recorded_payload
