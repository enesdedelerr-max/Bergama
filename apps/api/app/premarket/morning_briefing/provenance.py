"""Provenance Specification ``morning-briefing.provenance.v1``."""

from __future__ import annotations

from app.premarket.morning_briefing.models import BriefingProvenance
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


def build_config_fingerprint(request: ValidatedBriefingRequest) -> str:
    """Deterministic fingerprint of configuration and Policy Version binding."""
    if request.config.digest_method_id != DIGEST_METHOD_V1:
        msg = f"unsupported digest_method_id: {request.config.digest_method_id}"
        raise ValueError(msg)
    return strategy_sha256(
        {
            "config": request.config.model_dump(mode="python"),
            "policy_version_id": POLICY_VERSION_V1,
            "ordering_preservation_policy_id": ORDERING_PRESERVATION_POLICY_V1,
            "identity_specification_id": IDENTITY_SPECIFICATION_V1,
            "provenance_specification_id": PROVENANCE_SPECIFICATION_V1,
            "digest_method_id": DIGEST_METHOD_V1,
        }
    )


def build_input_fingerprint(request: ValidatedBriefingRequest) -> str:
    """Deterministic fingerprint of authorized inputs actually consumed."""
    return strategy_sha256(
        {
            "as_of": request.as_of,
            "ordered_score_record_ids": [
                record.score_record_id for record in request.scores.records
            ],
            "upstream_scoring_collection": request.scores.model_dump(mode="python"),
            "upstream_scoring_policy_version_id": SCORING_POLICY_VERSION_V1,
            "ordering_preservation_policy_id": ORDERING_PRESERVATION_POLICY_V1,
        }
    )


def build_briefing_provenance(request: ValidatedBriefingRequest) -> BriefingProvenance:
    """Build collection-level Morning Briefing provenance."""
    source_identifiers = tuple(record.score_record_id for record in request.scores.records)
    return BriefingProvenance(
        policy_version_id=POLICY_VERSION_V1,
        ordering_preservation_policy_id=ORDERING_PRESERVATION_POLICY_V1,
        identity_specification_id=IDENTITY_SPECIFICATION_V1,
        provenance_specification_id=PROVENANCE_SPECIFICATION_V1,
        as_of=request.as_of,
        config_fingerprint=build_config_fingerprint(request),
        input_fingerprint=build_input_fingerprint(request),
        source_identifiers=source_identifiers,
        upstream_scoring_policy_version_id=request.scores.provenance.policy_version_id,
        upstream_scoring_weight_profile_id=request.scores.provenance.weight_profile_id,
        upstream_scoring_ordering_policy_id=request.scores.provenance.ordering_policy_id,
        upstream_scoring_config_fingerprint=request.scores.provenance.config_fingerprint,
        upstream_scoring_input_fingerprint=request.scores.provenance.input_fingerprint,
    )
