"""Deterministic Premarket Analyst projection pipeline."""

from __future__ import annotations

from app.premarket_analyst.errors import PremarketAnalystPipelineIsolationError
from app.premarket_analyst.models import PremarketAnalystArtifact
from app.premarket_analyst.validate_input import ValidatedAnalystRequest
from app.premarket_analyst.validate_output import validate_analyst_output


def run_analyst_pipeline(request: ValidatedAnalystRequest) -> PremarketAnalystArtifact:
    """Execute projection pipeline once over validated upstream outputs."""
    if not isinstance(request, ValidatedAnalystRequest):
        raise PremarketAnalystPipelineIsolationError(detail="unvalidated_request")

    # Local import avoids circular dependency with engine.project_analyst.
    from app.premarket_analyst.engine import assemble_projection

    artifact = assemble_projection(request)
    return validate_analyst_output(artifact, request=request)
