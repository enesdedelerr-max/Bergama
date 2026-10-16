"""Identity specification ``premarket-analyst.identity.v1``."""

from __future__ import annotations

from app.premarket_analyst.errors import PremarketAnalystUnsupportedPolicyError
from app.premarket_analyst.policy import (
    ANALYST_DEFINITION_VERSION_V1,
    DIGEST_METHOD_V1,
    IDENTITY_SPECIFICATION_V1,
    ORDERING_POLICY_V1,
    POLICY_VERSION_V1,
    PROVENANCE_SPECIFICATION_V1,
)
from app.premarket_analyst.validate_input import ValidatedAnalystRequest
from app.strategy.keys import strategy_sha256


def build_analyst_artifact_id(request: ValidatedAnalystRequest) -> str:
    """Return sha256 hex analyst artifact identity over the canonical v1 payload."""
    if request.config.digest_method_id != DIGEST_METHOD_V1:
        raise PremarketAnalystUnsupportedPolicyError(
            detail=f"unsupported_digest_method:{request.config.digest_method_id}"
        )
    return strategy_sha256(_canonical_identity_payload(request))


def _canonical_identity_payload(request: ValidatedAnalystRequest) -> dict[str, object]:
    return {
        "schema": IDENTITY_SPECIFICATION_V1,
        "analyst_definition_version": ANALYST_DEFINITION_VERSION_V1,
        "policy_version_id": POLICY_VERSION_V1,
        "ordering_policy_id": ORDERING_POLICY_V1,
        "provenance_specification_id": PROVENANCE_SPECIFICATION_V1,
        "as_of": request.as_of,
        "configuration": request.config.model_dump(mode="python"),
        "membership_complete": request.membership_complete,
        "watchlist_membership": [entry.instrument_key for entry in request.watchlist.entries],
        "watchlist_provenance": request.watchlist.provenance.model_dump(mode="python"),
        "gaps_fingerprint": (
            None if request.gaps is None else request.gaps.provenance.input_fingerprint
        ),
        "catalysts_fingerprint": (
            None if request.catalysts is None else request.catalysts.provenance.input_fingerprint
        ),
        "scores_fingerprint": (
            None if request.scores is None else request.scores.provenance.input_fingerprint
        ),
        "briefing_id": None if request.briefing is None else request.briefing.briefing_id,
        "dashboard_output_id": (
            None if request.dashboard is None else request.dashboard.dashboard_output_id
        ),
        "upstream_pipeline_failure_identity": request.upstream_pipeline_failure_identity,
        "unsupported_instrument_keys": list(request.unsupported_instrument_keys),
    }
