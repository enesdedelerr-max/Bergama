"""Thin in-process Intelligence Pipeline replay and equality (Issue #130)."""

from __future__ import annotations

from typing import Any

from app.intelligence_pipeline.errors import PipelineReplayInequalityError
from app.intelligence_pipeline.models import PipelineOutcome, PipelineResult
from app.intelligence_pipeline.orchestrator import run_intelligence_pipeline
from app.intelligence_pipeline.policy import FAILURE_DETAIL_MAX_LENGTH


def replay_intelligence_pipeline(
    request: object,
    *,
    expected: PipelineResult,
) -> PipelineResult:
    """Re-execute through the public Pipeline boundary and assert deterministic equality."""
    actual = run_intelligence_pipeline(request)
    assert_replay_equal(expected, actual)
    return actual


def assert_replay_equal(expected: PipelineResult, actual: PipelineResult) -> None:
    """Fail closed when replay projection fields diverge. Not a PipelineOutcome."""
    expected_proj = _replay_equality_projection(expected)
    actual_proj = _replay_equality_projection(actual)
    mismatches: list[str] = []
    for key in sorted(set(expected_proj) | set(actual_proj)):
        if expected_proj.get(key) != actual_proj.get(key):
            mismatches.append(key)
    if mismatches:
        bounded = tuple(mismatches[:FAILURE_DETAIL_MAX_LENGTH])
        raise PipelineReplayInequalityError(
            detail=f"replay_mismatch:{','.join(bounded)}",
            mismatches=bounded,
        )


def _replay_equality_projection(result: PipelineResult) -> dict[str, Any]:
    """Deterministic equality projection for Sprint-13 replay policy."""
    prov = result.provenance
    projection: dict[str, Any] = {
        "outcome": result.outcome.value,
        "as_of": result.as_of,
        "bindings": (
            result.bindings.model_dump(mode="python") if result.bindings is not None else None
        ),
        "pipeline_fingerprint": prov.pipeline_fingerprint,
        "executed_stages": prov.executed_stages,
        "provenance_outcome": prov.outcome.value if prov.outcome is not None else None,
        "provenance_failed_stage": prov.failed_stage,
        "watchlist_config_fingerprint": prov.watchlist_config_fingerprint,
        "watchlist_input_fingerprint": prov.watchlist_input_fingerprint,
        "gap_config_fingerprint": prov.gap_config_fingerprint,
        "gap_input_fingerprint": prov.gap_input_fingerprint,
        "catalyst_config_fingerprint": prov.catalyst_config_fingerprint,
        "catalyst_input_fingerprint": prov.catalyst_input_fingerprint,
        "score_config_fingerprint": prov.score_config_fingerprint,
        "score_input_fingerprint": prov.score_input_fingerprint,
        "briefing_config_fingerprint": prov.briefing_config_fingerprint,
        "briefing_input_fingerprint": prov.briefing_input_fingerprint,
        "dashboard_config_fingerprint": prov.dashboard_config_fingerprint,
        "dashboard_input_fingerprint": prov.dashboard_input_fingerprint,
        "human_review_output_id": prov.human_review_output_id,
        "human_review_config_fingerprint": prov.human_review_config_fingerprint,
        "human_review_input_fingerprint": prov.human_review_input_fingerprint,
        "recorded_attestation_fingerprint": prov.recorded_attestation_fingerprint,
        "ade_decision_id": prov.ade_decision_id,
        "ade_outcome_kind": (
            prov.ade_outcome_kind.value if prov.ade_outcome_kind is not None else None
        ),
        "ade_evidence_fingerprint": prov.ade_evidence_fingerprint,
        "failed_stage": result.failed_stage,
        "failure_error_type": result.failure_error_type,
        "failure_detail": result.failure_detail,
        # Presence / empty-object distinction (None ≠ empty collection).
        "watchlist_present": result.watchlist is not None,
        "gaps_present": result.gaps is not None,
        "catalysts_present": result.catalysts is not None,
        "scores_present": result.scores is not None,
        "briefing_present": result.briefing is not None,
        "dashboard_present": result.dashboard is not None,
        "human_review_present": result.human_review is not None,
        "ade_present": result.ade is not None,
        "gaps_empty": (len(result.gaps.records) == 0 if result.gaps is not None else None),
        "catalysts_empty": (
            len(result.catalysts.records) == 0 if result.catalysts is not None else None
        ),
    }

    if result.outcome is PipelineOutcome.ADMISSION_REJECTED:
        # Admission-rejected runs may lack bindings / fingerprint; do not require them.
        projection.pop("pipeline_fingerprint", None)
        projection["bindings"] = None

    return projection
