"""Post-condition Validation Layer for Morning Briefing."""

from __future__ import annotations

from decimal import Decimal

from app.premarket.errors import BriefingDomainError, BriefingInvariantError
from app.premarket.morning_briefing.identity import build_briefing_id
from app.premarket.morning_briefing.models import BriefingCollection
from app.premarket.morning_briefing.ordering import assert_ordering_preserved
from app.premarket.morning_briefing.policy import (
    DIGEST_METHOD_V1,
    IDENTITY_SPECIFICATION_V1,
    ORDERING_PRESERVATION_POLICY_V1,
    POLICY_VERSION_V1,
    PROVENANCE_SPECIFICATION_V1,
    REQUIRED_UPSTREAM_SCORING_POLICY_VERSION_ID,
)
from app.premarket.morning_briefing.provenance import build_briefing_provenance
from app.premarket.morning_briefing.validate_input import ValidatedBriefingRequest
from app.premarket.scoring.policy import WEIGHT_PROFILE_DEFAULT_V1


def validate_briefing_collection(
    collection: BriefingCollection,
    *,
    request: ValidatedBriefingRequest,
) -> BriefingCollection:
    """Enforce Policy Version v1 post-conditions before emission."""
    if collection.as_of != request.as_of:
        raise BriefingInvariantError(detail="as_of_mismatch")
    if collection.policy_version_id != POLICY_VERSION_V1:
        raise BriefingInvariantError(detail="policy_version_mismatch")
    if collection.ordering_preservation_policy_id != ORDERING_PRESERVATION_POLICY_V1:
        raise BriefingInvariantError(detail="ordering_preservation_policy_mismatch")
    if collection.provenance.policy_version_id != POLICY_VERSION_V1:
        raise BriefingInvariantError(detail="provenance_policy_version_mismatch")
    if collection.provenance.ordering_preservation_policy_id != ORDERING_PRESERVATION_POLICY_V1:
        raise BriefingInvariantError(detail="provenance_ordering_policy_mismatch")
    if collection.provenance.identity_specification_id != IDENTITY_SPECIFICATION_V1:
        raise BriefingInvariantError(detail="identity_specification_mismatch")
    if collection.provenance.provenance_specification_id != PROVENANCE_SPECIFICATION_V1:
        raise BriefingInvariantError(detail="provenance_specification_mismatch")
    if collection.provenance.as_of != request.as_of:
        raise BriefingInvariantError(detail="provenance_as_of_mismatch")
    if request.config.digest_method_id != DIGEST_METHOD_V1:
        raise BriefingInvariantError(detail="digest_method_mismatch")

    expected_provenance = build_briefing_provenance(request)
    if collection.provenance != expected_provenance:
        raise BriefingInvariantError(detail="provenance_mismatch")

    expected_briefing_id = build_briefing_id(request)
    if collection.briefing_id != expected_briefing_id:
        raise BriefingInvariantError(detail="briefing_id_mismatch")

    assert_ordering_preserved(scores=request.scores, records=collection.records)

    if collection.provenance.upstream_scoring_policy_version_id != (
        REQUIRED_UPSTREAM_SCORING_POLICY_VERSION_ID
    ):
        raise BriefingInvariantError(detail="upstream_scoring_policy_mismatch")
    if collection.provenance.upstream_scoring_weight_profile_id != WEIGHT_PROFILE_DEFAULT_V1:
        raise BriefingInvariantError(detail="upstream_weight_profile_mismatch")

    expected_source_ids = tuple(record.score_record_id for record in request.scores.records)
    if collection.provenance.source_identifiers != expected_source_ids:
        raise BriefingInvariantError(detail="source_identifiers_mismatch")

    for index, (briefing_record, score_record) in enumerate(
        zip(collection.records, request.scores.records, strict=True)
    ):
        if briefing_record.local_symbol != score_record.local_symbol:
            raise BriefingInvariantError(detail=f"local_symbol_mutation:{index}")
        if briefing_record.components != score_record.components:
            raise BriefingInvariantError(detail=f"components_mutation:{index}")
        if briefing_record.scoring_policy_version_id != score_record.policy_version_id:
            raise BriefingInvariantError(detail=f"scoring_policy_mutation:{index}")
        if briefing_record.scoring_weight_profile_id != score_record.weight_profile_id:
            raise BriefingInvariantError(detail=f"scoring_weight_mutation:{index}")
        if briefing_record.scoring_as_of != score_record.as_of:
            raise BriefingInvariantError(detail=f"scoring_as_of_mutation:{index}")
        if briefing_record.watchlist_rank != score_record.watchlist_rank:
            raise BriefingInvariantError(detail=f"watchlist_rank_mutation:{index}")
        if briefing_record.watchlist_rule_id != score_record.watchlist_rule_id:
            raise BriefingInvariantError(detail=f"watchlist_rule_id_mutation:{index}")
        if briefing_record.gap_record_id != score_record.gap_record_id:
            raise BriefingInvariantError(detail=f"gap_record_id_mutation:{index}")
        if briefing_record.catalyst_source_identifiers != score_record.catalyst_source_identifiers:
            raise BriefingInvariantError(detail=f"catalyst_source_identifiers_mutation:{index}")
        if not briefing_record.score.is_finite():
            raise BriefingDomainError(detail=f"non_finite_score:{briefing_record.instrument_key}")
        if briefing_record.score < Decimal("0") or briefing_record.score > Decimal("1"):
            raise BriefingDomainError(
                detail=f"score_out_of_domain:{briefing_record.instrument_key}"
            )

    return collection
