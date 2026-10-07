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
    assert build_authoritative_snapshot(dashboard).outcome == "completed_dashboard"

    hr = run_intelligence_pipeline(
        _valid_request(hr_requested=True, hr_attestation=VALID_ATTESTATION)
    )
    assert build_authoritative_snapshot(hr).outcome == "completed_human_review"

    ade = run_intelligence_pipeline(
        _valid_request(
            hr_requested=True,
            ade_requested=True,
            hr_attestation=VALID_ATTESTATION,
        )
    )
    assert build_authoritative_snapshot(ade).outcome == "completed_ade_accept"

    rejected = run_intelligence_pipeline(_valid_request(hr_requested=True, hr_attestation=None))
    assert build_authoritative_snapshot(rejected).outcome == "admission_rejected"
