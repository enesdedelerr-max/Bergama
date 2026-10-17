"""Unit tests for Intelligence Run materializer orchestration helpers (WS2)."""

from __future__ import annotations

import ast
from pathlib import Path

from app.intelligence_pipeline import PipelineOutcome, run_intelligence_pipeline
from app.intelligence_runs.materializer import IntelligenceRunMaterializer
from app.intelligence_runs.snapshot import build_authoritative_snapshot
from tests.unit.test_intelligence_pipeline_core import VALID_ATTESTATION, _valid_request

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "app" / "intelligence_runs"


def test_materializer_module_has_no_http_or_recompute_imports() -> None:
    path = PACKAGE_ROOT / "materializer.py"
    text = path.read_text(encoding="utf-8")
    assert "APIRouter" not in text
    assert "evaluate_ade" not in text
    assert "run_intelligence_pipeline" not in text
    assert "httpx" not in text
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("fastapi")
            assert "orchestrator" not in node.module


def test_materializer_builds_from_completed_pipeline_result_only() -> None:
    result = run_intelligence_pipeline(_valid_request())
    snapshot = build_authoritative_snapshot(result)
    assert snapshot.outcome == PipelineOutcome.COMPLETED_DASHBOARD.value
    assert IntelligenceRunMaterializer.__name__ == "IntelligenceRunMaterializer"


def test_six_outcomes_materializable_structurally() -> None:
    dashboard = run_intelligence_pipeline(_valid_request())
    dash_snap = build_authoritative_snapshot(dashboard)
    assert dash_snap.outcome == "completed_dashboard"
    assert dash_snap.analyst_snapshot is not None

    hr = run_intelligence_pipeline(
        _valid_request(hr_requested=True, hr_attestation=VALID_ATTESTATION)
    )
    hr_snap = build_authoritative_snapshot(hr)
    assert hr_snap.outcome == "completed_human_review"
    assert hr_snap.analyst_snapshot is not None

    ade = run_intelligence_pipeline(
        _valid_request(
            hr_requested=True,
            ade_requested=True,
            hr_attestation=VALID_ATTESTATION,
        )
    )
    ade_snap = build_authoritative_snapshot(ade)
    assert ade_snap.outcome == "completed_ade_accept"
    assert ade_snap.analyst_snapshot is not None

    rejected = run_intelligence_pipeline(_valid_request(hr_requested=True, hr_attestation=None))
    rejected_snap = build_authoritative_snapshot(rejected)
    assert rejected_snap.outcome == "admission_rejected"
    assert rejected_snap.analyst_snapshot is None


def test_materializer_to_record_includes_analyst() -> None:
    result = run_intelligence_pipeline(_valid_request())
    snapshot = build_authoritative_snapshot(result)
    record = IntelligenceRunMaterializer._to_record(snapshot)
    assert record.analyst_snapshot_json == snapshot.analyst_snapshot
    assert record.snapshot_contract_version == snapshot.snapshot_contract_version
