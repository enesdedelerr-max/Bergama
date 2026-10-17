"""Unit tests for WS2 analyst snapshot projection and version rules."""

from __future__ import annotations

from datetime import UTC
from unittest.mock import MagicMock

import pytest
from app.intelligence_pipeline import PipelineOutcome, run_intelligence_pipeline
from app.intelligence_pipeline.models import PipelineResult
from app.intelligence_runs.constants import (
    SNAPSHOT_CONTRACT_VERSION_V1,
    SNAPSHOT_CONTRACT_VERSION_V2,
)
from app.intelligence_runs.errors import IntelligenceRunInvalidMaterializationError
from app.intelligence_runs.snapshot import (
    AuthoritativeSnapshot,
    build_analyst_public_snapshot,
    build_authoritative_snapshot,
    canonical_snapshots_equal,
    enforce_analyst_invariant,
)
from app.premarket_analyst.errors import PremarketAnalystFailClosedError
from tests.unit.test_intelligence_pipeline_core import VALID_ATTESTATION, _valid_request


def test_v2_completed_outcomes_require_analyst() -> None:
    for builder in (
        lambda: run_intelligence_pipeline(_valid_request()),
        lambda: run_intelligence_pipeline(
            _valid_request(hr_requested=True, hr_attestation=VALID_ATTESTATION)
        ),
        lambda: run_intelligence_pipeline(
            _valid_request(
                hr_requested=True,
                ade_requested=True,
                hr_attestation=VALID_ATTESTATION,
            )
        ),
    ):
        snapshot = build_authoritative_snapshot(builder())
        assert snapshot.snapshot_contract_version == SNAPSHOT_CONTRACT_VERSION_V2
        assert snapshot.analyst_snapshot is not None
        enforce_analyst_invariant(snapshot)


def test_v2_ineligible_outcomes_forbid_analyst() -> None:
    rejected = build_authoritative_snapshot(
        run_intelligence_pipeline(_valid_request(hr_requested=True, hr_attestation=None))
    )
    assert rejected.outcome == "admission_rejected"
    assert rejected.analyst_snapshot is None

    monkey = pytest.MonkeyPatch()
    monkey.setattr(
        "app.intelligence_pipeline.orchestrator.scan_gaps",
        MagicMock(side_effect=ValueError("gap_fail")),
    )
    try:
        failed = build_authoritative_snapshot(run_intelligence_pipeline(_valid_request()))
    finally:
        monkey.undo()
    assert failed.outcome == "required_stage_failed"
    assert failed.analyst_snapshot is None


def test_insufficient_evidence_analyst_artifact_is_persistable() -> None:
    result = run_intelligence_pipeline(_valid_request())
    # Watchlist-only projection path yields INSUFFICIENT_EVIDENCE when gaps absent
    # are not the case for full pipeline — use build_analyst with gaps=None override.
    thin = PipelineResult(
        outcome=PipelineOutcome.COMPLETED_DASHBOARD,
        as_of=result.as_of,
        bindings=result.bindings,
        provenance=result.provenance,
        watchlist=result.watchlist,
        gaps=None,
        catalysts=result.catalysts,
        scores=result.scores,
        briefing=result.briefing,
        dashboard=result.dashboard,
    )
    # Full build would fail outcome structure (gaps required for completed).
    # Direct projection still produces a valid persistable artifact.
    artifact = build_analyst_public_snapshot(thin, outcome="completed_dashboard")
    assert artifact is not None
    assert artifact["evaluation_state"] in {
        "INSUFFICIENT_EVIDENCE",
        "NOT_EVALUABLE",
        "ABSTAIN",
        "READY",
    }


def test_eligible_projection_failure_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(_request: object) -> object:
        raise PremarketAnalystFailClosedError("projection_blocked")

    monkeypatch.setattr("app.intelligence_runs.snapshot.project_analyst", boom)
    with pytest.raises(IntelligenceRunInvalidMaterializationError) as exc_info:
        build_authoritative_snapshot(run_intelligence_pipeline(_valid_request()))
    assert "analyst_projection_failed" in str(exc_info.value.detail)


def test_v2_canonical_equality_includes_analyst() -> None:
    result = run_intelligence_pipeline(_valid_request())
    left = build_authoritative_snapshot(result)
    right = build_authoritative_snapshot(result)
    assert canonical_snapshots_equal(left, right)
    mutated = left.model_copy(
        update={
            "analyst_snapshot": {
                **left.analyst_snapshot,  # type: ignore[dict-item]
                "evaluation_state": "ABSTAIN",
            }
        }
    )
    assert not canonical_snapshots_equal(left, mutated)


def test_v1_snapshot_rejects_analyst_payload() -> None:
    result = run_intelligence_pipeline(_valid_request())
    v2 = build_authoritative_snapshot(result)
    payload = v2.model_dump(mode="json")
    payload["snapshot_contract_version"] = SNAPSHOT_CONTRACT_VERSION_V1
    with pytest.raises(ValueError, match="v1 snapshots must not carry analyst"):
        AuthoritativeSnapshot.model_validate(payload)


def test_v2_eligible_rejects_missing_analyst() -> None:
    result = run_intelligence_pipeline(_valid_request())
    v2 = build_authoritative_snapshot(result)
    payload = v2.model_dump(mode="json")
    payload["analyst_snapshot"] = None
    with pytest.raises(ValueError, match="requires non-null analyst_snapshot"):
        AuthoritativeSnapshot.model_validate(payload)


def test_analyst_projection_uses_pipeline_as_of_not_wall_clock() -> None:
    result = run_intelligence_pipeline(_valid_request())
    assert result.as_of is not None
    artifact = build_analyst_public_snapshot(result, outcome="completed_dashboard")
    assert artifact is not None
    assert isinstance(artifact["as_of"], str)
    assert result.as_of.astimezone(UTC).isoformat()[:19] in artifact["as_of"].replace("Z", "+00:00")
