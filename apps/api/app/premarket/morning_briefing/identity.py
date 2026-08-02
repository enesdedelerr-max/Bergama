"""Identity Specification ``morning-briefing.identity.v1``."""

from __future__ import annotations

from app.premarket.morning_briefing.models import BriefingConfig
from app.premarket.morning_briefing.policy import (
    DIGEST_METHOD_V1,
    IDENTITY_SPECIFICATION_V1,
    ORDERING_PRESERVATION_POLICY_V1,
    POLICY_VERSION_V1,
    PROVENANCE_SPECIFICATION_V1,
)
from app.premarket.morning_briefing.validate_input import ValidatedBriefingRequest
from app.premarket.scoring.policy import POLICY_VERSION_V1 as SCORING_POLICY_VERSION_V1
from app.strategy.keys import strategy_sha256


def build_briefing_id(request: ValidatedBriefingRequest) -> str:
    """Return sha256 hex Morning Briefing identity over the canonical v1 payload."""
    if request.config.digest_method_id != DIGEST_METHOD_V1:
        msg = f"unsupported digest_method_id: {request.config.digest_method_id}"
        raise ValueError(msg)
    return strategy_sha256(_canonical_identity_payload(request))


def _canonical_identity_payload(request: ValidatedBriefingRequest) -> dict[str, object]:
    config: BriefingConfig = request.config
    return {
        "schema": IDENTITY_SPECIFICATION_V1,
        "policy_version_id": POLICY_VERSION_V1,
        "ordering_preservation_policy_id": ORDERING_PRESERVATION_POLICY_V1,
        "provenance_specification_id": PROVENANCE_SPECIFICATION_V1,
        "as_of": request.as_of,
        "configuration": config.model_dump(mode="python"),
        "upstream_scoring_policy_version_id": SCORING_POLICY_VERSION_V1,
        "ordered_score_record_ids": [record.score_record_id for record in request.scores.records],
        "upstream_scoring_collection_provenance": request.scores.provenance.model_dump(
            mode="python"
        ),
    }
