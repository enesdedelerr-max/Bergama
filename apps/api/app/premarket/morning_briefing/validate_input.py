"""Input Validation and Policy Version Binding for Morning Briefing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.premarket.errors import (
    BriefingConflictError,
    BriefingDomainError,
    BriefingUnsupportedPolicyError,
    BriefingValidationError,
    PremarketDisabledError,
)
from app.premarket.morning_briefing.models import BriefingConfig, BriefingRequest
from app.premarket.morning_briefing.policy import (
    DIGEST_METHOD_V1,
    IDENTITY_SPECIFICATION_V1,
    ORDERING_PRESERVATION_POLICY_V1,
    POLICY_VERSION_V1,
    PROVENANCE_SPECIFICATION_V1,
    REQUIRED_UPSTREAM_SCORING_POLICY_VERSION_ID,
)
from app.premarket.scoring.models import ScoreCollection, ScoreRecord
from app.premarket.scoring.policy import (
    POLICY_VERSION_V1 as SCORING_POLICY_VERSION_V1,
)
from app.premarket.scoring.policy import (
    WEIGHT_PROFILE_DEFAULT_V1,
)
from app.premarket.settings import PremarketSettings


@dataclass(frozen=True, slots=True)
class ValidatedBriefingRequest:
    """Request admitted through Input Validation and Policy Version Binding."""

    scores: ScoreCollection
    as_of: datetime
    config: BriefingConfig


def validate_briefing_request(
    request: BriefingRequest,
    *,
    settings: PremarketSettings | None = None,
) -> ValidatedBriefingRequest:
    """Admit only Governance Decision #2 / Policy Version v1-legal requests."""
    if settings is not None and not settings.enabled:
        raise PremarketDisabledError(detail="premarket_disabled")

    _assert_policy_binding(request.config)
    _assert_pit(request)
    _assert_upstream_scoring_collection(request.scores, as_of=request.as_of)

    return ValidatedBriefingRequest(
        scores=request.scores,
        as_of=request.as_of,
        config=request.config,
    )


def _assert_policy_binding(config: BriefingConfig) -> None:
    if config.policy_version_id != POLICY_VERSION_V1:
        raise BriefingUnsupportedPolicyError(
            detail=f"unsupported_policy:{config.policy_version_id}"
        )
    if config.ordering_preservation_policy_id != ORDERING_PRESERVATION_POLICY_V1:
        raise BriefingUnsupportedPolicyError(
            detail=f"unsupported_ordering_preservation:{config.ordering_preservation_policy_id}"
        )
    if config.identity_specification_id != IDENTITY_SPECIFICATION_V1:
        raise BriefingUnsupportedPolicyError(
            detail=f"unsupported_identity_specification:{config.identity_specification_id}"
        )
    if config.provenance_specification_id != PROVENANCE_SPECIFICATION_V1:
        raise BriefingUnsupportedPolicyError(
            detail=f"unsupported_provenance_specification:{config.provenance_specification_id}"
        )
    if config.digest_method_id != DIGEST_METHOD_V1:
        raise BriefingUnsupportedPolicyError(
            detail=f"unsupported_digest_method:{config.digest_method_id}"
        )


def _assert_pit(request: BriefingRequest) -> None:
    if request.scores.as_of != request.as_of:
        raise BriefingConflictError(
            detail=(
                f"cross_pit_scores:{request.scores.as_of.isoformat()}:{request.as_of.isoformat()}"
            )
        )


def _assert_upstream_scoring_collection(
    scores: ScoreCollection,
    *,
    as_of: datetime,
) -> None:
    if scores.provenance.policy_version_id != REQUIRED_UPSTREAM_SCORING_POLICY_VERSION_ID:
        raise BriefingUnsupportedPolicyError(
            detail=f"upstream_scoring_policy_mismatch:{scores.provenance.policy_version_id}"
        )
    if scores.provenance.weight_profile_id != WEIGHT_PROFILE_DEFAULT_V1:
        raise BriefingValidationError(
            detail=f"upstream_weight_profile_mismatch:{scores.provenance.weight_profile_id}"
        )
    if scores.as_of != as_of:
        raise BriefingConflictError(
            detail=f"cross_pit_scores:{scores.as_of.isoformat()}:{as_of.isoformat()}"
        )

    seen_ids: set[str] = set()
    for record in scores.records:
        _assert_upstream_score_record(record, as_of=as_of)
        if record.score_record_id in seen_ids:
            raise BriefingValidationError(
                detail=f"duplicate_score_record_id:{record.score_record_id}"
            )
        seen_ids.add(record.score_record_id)


def _assert_upstream_score_record(record: ScoreRecord, *, as_of: datetime) -> None:
    if record.policy_version_id != SCORING_POLICY_VERSION_V1:
        raise BriefingUnsupportedPolicyError(
            detail=f"record_scoring_policy_mismatch:{record.instrument_key}"
        )
    if record.weight_profile_id != WEIGHT_PROFILE_DEFAULT_V1:
        raise BriefingValidationError(
            detail=f"record_weight_profile_mismatch:{record.instrument_key}"
        )
    if record.as_of != as_of:
        raise BriefingConflictError(
            detail=(
                "cross_pit_score_record:"
                f"{record.instrument_key}:{record.as_of.isoformat()}:{as_of.isoformat()}"
            )
        )
    if not record.score.is_finite():
        raise BriefingDomainError(detail=f"non_finite_score:{record.instrument_key}")
    if record.score < Decimal("0") or record.score > Decimal("1"):
        raise BriefingDomainError(detail=f"score_out_of_domain:{record.instrument_key}")
    if len(record.score_record_id) != 64:
        raise BriefingValidationError(detail=f"invalid_score_record_id:{record.instrument_key}")
