"""Input validation and PIT admission for Premarket Analyst projection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.dashboard.models import DashboardPresentationOutput
from app.market_data.timing import require_utc_aware
from app.premarket.catalyst.models import CatalystCollection
from app.premarket.gap.models import GapCollection
from app.premarket.morning_briefing import BriefingCollection
from app.premarket.scoring.models import ScoreCollection
from app.premarket.watchlist.models import Watchlist
from app.premarket_analyst.errors import (
    PremarketAnalystFailClosedError,
    PremarketAnalystPitConflictError,
    PremarketAnalystUnauthorizedInputError,
    PremarketAnalystUnsupportedPolicyError,
    PremarketAnalystValidationError,
)
from app.premarket_analyst.models import AnalystConfig, AnalystProjectionRequest
from app.premarket_analyst.policy import (
    ANALYST_DEFINITION_VERSION_V1,
    DIGEST_METHOD_V1,
    IDENTITY_SPECIFICATION_V1,
    ORDERING_POLICY_V1,
    POLICY_VERSION_V1,
    PROVENANCE_SPECIFICATION_V1,
)


@dataclass(frozen=True, slots=True)
class ValidatedAnalystRequest:
    """Request admitted for deterministic analyst projection."""

    as_of: datetime
    watchlist: Watchlist
    config: AnalystConfig
    gaps: GapCollection | None
    catalysts: CatalystCollection | None
    scores: ScoreCollection | None
    briefing: BriefingCollection | None
    dashboard: DashboardPresentationOutput | None
    membership_complete: bool
    upstream_pipeline_failure_identity: str | None
    unsupported_instrument_keys: tuple[str, ...]


def validate_analyst_request(request: AnalystProjectionRequest) -> ValidatedAnalystRequest:
    """Admit only Policy-compatible projection requests. Fail closed on malformed input."""
    _assert_no_unauthorized_input(request)
    _assert_policy_binding(request.config)
    as_of = require_utc_aware(request.as_of, field_name="as_of")
    _assert_pit(request, as_of=as_of)
    return ValidatedAnalystRequest(
        as_of=as_of,
        watchlist=request.watchlist,
        config=request.config,
        gaps=request.gaps,
        catalysts=request.catalysts,
        scores=request.scores,
        briefing=request.briefing,
        dashboard=request.dashboard,
        membership_complete=request.membership_complete,
        upstream_pipeline_failure_identity=request.upstream_pipeline_failure_identity,
        unsupported_instrument_keys=request.unsupported_instrument_keys,
    )


def _assert_no_unauthorized_input(request: AnalystProjectionRequest) -> None:
    extra = getattr(request, "__pydantic_extra__", None)
    if extra:
        raise PremarketAnalystUnauthorizedInputError(
            detail=f"unexpected_extra_fields:{sorted(extra)}"
        )


def _assert_policy_binding(config: AnalystConfig) -> None:
    if config.analyst_definition_version != ANALYST_DEFINITION_VERSION_V1:
        raise PremarketAnalystUnsupportedPolicyError(
            detail=f"unsupported_definition:{config.analyst_definition_version}"
        )
    if config.policy_version_id != POLICY_VERSION_V1:
        raise PremarketAnalystUnsupportedPolicyError(
            detail=f"unsupported_policy:{config.policy_version_id}"
        )
    if config.identity_specification_id != IDENTITY_SPECIFICATION_V1:
        raise PremarketAnalystUnsupportedPolicyError(
            detail=f"unsupported_identity:{config.identity_specification_id}"
        )
    if config.provenance_specification_id != PROVENANCE_SPECIFICATION_V1:
        raise PremarketAnalystUnsupportedPolicyError(
            detail=f"unsupported_provenance:{config.provenance_specification_id}"
        )
    if config.digest_method_id != DIGEST_METHOD_V1:
        raise PremarketAnalystUnsupportedPolicyError(
            detail=f"unsupported_digest:{config.digest_method_id}"
        )
    if config.ordering_policy_id != ORDERING_POLICY_V1:
        raise PremarketAnalystUnsupportedPolicyError(
            detail=f"unsupported_ordering:{config.ordering_policy_id}"
        )


def _assert_pit(request: AnalystProjectionRequest, *, as_of: datetime) -> None:
    if request.watchlist.evaluation_timestamp > as_of:
        raise PremarketAnalystPitConflictError(detail="watchlist_evaluation_after_as_of")
    if request.gaps is not None:
        if request.gaps.as_of > as_of:
            raise PremarketAnalystPitConflictError(detail="gaps_as_of_after_request_as_of")
        for gap_record in request.gaps.records:
            if gap_record.as_of > as_of:
                raise PremarketAnalystPitConflictError(
                    detail=f"gap_as_of_after:{gap_record.gap_record_id}"
                )
            # known_at > as_of is handled in projection mapping (stale / no-lookahead exclusion)
            if gap_record.event_time > as_of:
                raise PremarketAnalystPitConflictError(
                    detail=f"gap_event_time_after_as_of:{gap_record.gap_record_id}"
                )
    if request.catalysts is not None:
        if request.catalysts.as_of > as_of:
            raise PremarketAnalystPitConflictError(detail="catalysts_as_of_after_request_as_of")
        for catalyst_record in request.catalysts.records:
            if catalyst_record.as_of > as_of:
                raise PremarketAnalystPitConflictError(
                    detail=f"catalyst_as_of_after:{catalyst_record.catalyst_record_id}"
                )
            # known_at > as_of → OIA-04 stale mapping (NOT_EVALUABLE + STALE_DATA)
            if catalyst_record.event_time > as_of:
                raise PremarketAnalystPitConflictError(
                    detail=f"catalyst_event_time_after_as_of:{catalyst_record.catalyst_record_id}"
                )
    if request.scores is not None:
        if request.scores.as_of > as_of:
            raise PremarketAnalystPitConflictError(detail="scores_as_of_after_request_as_of")
        for score_record in request.scores.records:
            if score_record.as_of > as_of:
                raise PremarketAnalystPitConflictError(
                    detail=f"score_as_of_after:{score_record.score_record_id}"
                )
    if request.briefing is not None and request.briefing.as_of > as_of:
        raise PremarketAnalystPitConflictError(detail="briefing_as_of_after_request_as_of")
    if request.dashboard is not None and request.dashboard.as_of > as_of:
        raise PremarketAnalystPitConflictError(detail="dashboard_as_of_after_request_as_of")


def coerce_analyst_request(request: AnalystProjectionRequest | object) -> AnalystProjectionRequest:
    if isinstance(request, AnalystProjectionRequest):
        return request
    try:
        return AnalystProjectionRequest.model_validate(request)
    except Exception as exc:
        raise PremarketAnalystFailClosedError(detail=f"malformed_request:{exc}") from exc


def require_validated_type(request: object) -> ValidatedAnalystRequest:
    if not isinstance(request, ValidatedAnalystRequest):
        raise PremarketAnalystValidationError(detail="unvalidated_request")
    return request
