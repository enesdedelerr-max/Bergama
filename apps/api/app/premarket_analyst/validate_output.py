"""Post-validation for Premarket Analyst artifacts."""

from __future__ import annotations

from app.premarket_analyst.errors import (
    PremarketAnalystDomainError,
    PremarketAnalystIdentityError,
    PremarketAnalystInvariantError,
    PremarketAnalystProvenanceError,
)
from app.premarket_analyst.identity import build_analyst_artifact_id
from app.premarket_analyst.models import PremarketAnalystArtifact
from app.premarket_analyst.policy import (
    ANALYST_DEFINITION_VERSION_V1,
    EVALUATION_STATE_COLLAPSE_ORDER,
    PROHIBITED_INVALIDATION_VOCABULARY,
    PROHIBITED_THESIS_VOCABULARY,
    RISK_FLAG_CATEGORIES,
)
from app.premarket_analyst.provenance import build_analyst_provenance
from app.premarket_analyst.validate_input import ValidatedAnalystRequest


def validate_analyst_output(
    artifact: PremarketAnalystArtifact,
    *,
    request: ValidatedAnalystRequest,
) -> PremarketAnalystArtifact:
    """Fail closed when artifact violates projection invariants."""
    if artifact.as_of != request.as_of:
        raise PremarketAnalystInvariantError(detail="as_of_mismatch")
    if artifact.analyst_definition_version != ANALYST_DEFINITION_VERSION_V1:
        raise PremarketAnalystDomainError(detail="definition_mismatch")
    if artifact.evaluation_state not in EVALUATION_STATE_COLLAPSE_ORDER:
        raise PremarketAnalystDomainError(
            detail=f"illegal_evaluation_state:{artifact.evaluation_state}"
        )

    expected_id = build_analyst_artifact_id(request)
    if artifact.analyst_artifact_id != expected_id:
        raise PremarketAnalystIdentityError(detail="analyst_artifact_id_mismatch")

    expected_provenance = build_analyst_provenance(request)
    if artifact.provenance.model_dump(mode="python") != expected_provenance.model_dump(
        mode="python"
    ):
        raise PremarketAnalystProvenanceError(detail="provenance_mismatch")

    membership = {entry.instrument_key for entry in request.watchlist.entries}
    artifact_membership = set(artifact.market_summary.watchlist_membership_refs)
    if artifact_membership != membership:
        raise PremarketAnalystDomainError(detail="watchlist_membership_mutation")
    if len(artifact.theses) != len(request.watchlist.entries):
        raise PremarketAnalystDomainError(detail="thesis_count_mismatch")

    for flag in artifact.risk_flags:
        if flag.category not in RISK_FLAG_CATEGORIES:
            raise PremarketAnalystDomainError(detail=f"illegal_risk_category:{flag.category}")

    _assert_no_prohibited_vocabulary(artifact)
    return artifact


def _assert_no_prohibited_vocabulary(artifact: PremarketAnalystArtifact) -> None:
    for thesis in artifact.theses:
        blobs = (
            thesis.supporting_evidence_refs
            + thesis.counter_evidence_refs
            + thesis.observed_conditions
            + thesis.informational_invalidation_conditions
            + thesis.uncertainty_markers
        )
        joined = " ".join(blobs)
        for term in PROHIBITED_THESIS_VOCABULARY:
            if term in joined:
                raise PremarketAnalystDomainError(detail=f"prohibited_thesis_vocabulary:{term}")
        for term in PROHIBITED_INVALIDATION_VOCABULARY:
            if term in joined:
                raise PremarketAnalystDomainError(
                    detail=f"prohibited_invalidation_vocabulary:{term}"
                )
