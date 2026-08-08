"""Input Validation through Authorized Input Admission for Dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.dashboard.errors import (
    DashboardDomainError,
    DashboardIdentityError,
    DashboardPitConflictError,
    DashboardProvenanceError,
    DashboardUnauthorizedInputError,
    DashboardUnsupportedPolicyError,
    DashboardUpstreamPolicyError,
    DashboardValidationError,
)
from app.dashboard.models import DashboardConfig, DashboardRequest
from app.dashboard.policy import (
    DIGEST_METHOD_V1,
    IDENTITY_SPECIFICATION_V1,
    ORDERING_PRESERVATION_POLICY_V1,
    POLICY_VERSION_V1,
    PRESENTATION_SELECTION_POLICY_V1,
    PROVENANCE_SPECIFICATION_V1,
    REQUIRED_UPSTREAM_BRIEFING_IDENTITY_SPECIFICATION_ID,
    REQUIRED_UPSTREAM_BRIEFING_POLICY_VERSION_ID,
    REQUIRED_UPSTREAM_BRIEFING_PROVENANCE_SPECIFICATION_ID,
)
from app.market_data.money import require_finite_decimal
from app.market_data.timing import require_utc_aware
from app.premarket.morning_briefing import BriefingCollection, BriefingRecord


@dataclass(frozen=True, slots=True)
class ValidatedDashboardRequest:
    """Request admitted through stages 1–5 of the Presentation Pipeline."""

    briefing: BriefingCollection
    as_of: datetime
    config: DashboardConfig


def validate_dashboard_request(request: DashboardRequest) -> ValidatedDashboardRequest:
    """Admit only Governance Decision #2 / Policy Version v1-legal requests.

    Semantic stage order:
    1. Input Validation
    2. Policy Version Binding
    3. Configuration Binding
    4. PIT Validation
    5. Authorized Input Admission
    """
    _assert_no_unauthorized_input(request)
    _assert_policy_and_configuration_binding(request.config)
    _assert_pit(request)
    _assert_authorized_morning_briefing(request.briefing, as_of=request.as_of)
    return ValidatedDashboardRequest(
        briefing=request.briefing,
        as_of=request.as_of,
        config=request.config,
    )


def _assert_no_unauthorized_input(request: DashboardRequest) -> None:
    extra = getattr(request, "__pydantic_extra__", None)
    if extra:
        raise DashboardUnauthorizedInputError(detail=f"unexpected_extra_fields:{sorted(extra)}")


def _assert_policy_and_configuration_binding(config: DashboardConfig) -> None:
    if config.policy_version_id != POLICY_VERSION_V1:
        raise DashboardUnsupportedPolicyError(
            detail=f"unsupported_policy:{config.policy_version_id}"
        )
    if config.ordering_preservation_policy_id != ORDERING_PRESERVATION_POLICY_V1:
        raise DashboardUnsupportedPolicyError(
            detail=f"unsupported_ordering_preservation:{config.ordering_preservation_policy_id}"
        )
    if config.identity_specification_id != IDENTITY_SPECIFICATION_V1:
        raise DashboardUnsupportedPolicyError(
            detail=f"unsupported_identity_specification:{config.identity_specification_id}"
        )
    if config.provenance_specification_id != PROVENANCE_SPECIFICATION_V1:
        raise DashboardUnsupportedPolicyError(
            detail=f"unsupported_provenance_specification:{config.provenance_specification_id}"
        )
    if config.digest_method_id != DIGEST_METHOD_V1:
        raise DashboardUnsupportedPolicyError(
            detail=f"unsupported_digest_method:{config.digest_method_id}"
        )
    if config.presentation_selection_policy_id != PRESENTATION_SELECTION_POLICY_V1:
        raise DashboardUnsupportedPolicyError(
            detail=(f"unsupported_presentation_selection:{config.presentation_selection_policy_id}")
        )


def _instant(value: datetime, *, field_name: str) -> datetime:
    return require_utc_aware(value, field_name=field_name)


def _assert_pit(request: DashboardRequest) -> None:
    request_instant = _instant(request.as_of, field_name="as_of")
    briefing_instant = _instant(request.briefing.as_of, field_name="briefing.as_of")
    if request_instant != briefing_instant:
        raise DashboardPitConflictError(
            detail=(f"cross_as_of:{request.briefing.as_of.isoformat()}:{request.as_of.isoformat()}")
        )


def _assert_authorized_morning_briefing(
    briefing: BriefingCollection,
    *,
    as_of: datetime,
) -> None:
    if briefing.policy_version_id != REQUIRED_UPSTREAM_BRIEFING_POLICY_VERSION_ID:
        raise DashboardUpstreamPolicyError(
            detail=f"upstream_briefing_policy_mismatch:{briefing.policy_version_id}"
        )
    if not _is_sha256_hex(briefing.briefing_id):
        raise DashboardIdentityError(detail="malformed_briefing_id")
    provenance = briefing.provenance
    if provenance.policy_version_id != REQUIRED_UPSTREAM_BRIEFING_POLICY_VERSION_ID:
        raise DashboardUpstreamPolicyError(
            detail=f"upstream_briefing_provenance_policy_mismatch:{provenance.policy_version_id}"
        )
    if provenance.identity_specification_id != REQUIRED_UPSTREAM_BRIEFING_IDENTITY_SPECIFICATION_ID:
        raise DashboardProvenanceError(
            detail=(
                "upstream_briefing_identity_specification_mismatch:"
                f"{provenance.identity_specification_id}"
            )
        )
    if provenance.provenance_specification_id != (
        REQUIRED_UPSTREAM_BRIEFING_PROVENANCE_SPECIFICATION_ID
    ):
        raise DashboardProvenanceError(
            detail=(
                "upstream_briefing_provenance_specification_mismatch:"
                f"{provenance.provenance_specification_id}"
            )
        )
    if not _is_sha256_hex(provenance.config_fingerprint):
        raise DashboardProvenanceError(detail="malformed_upstream_config_fingerprint")
    if not _is_sha256_hex(provenance.input_fingerprint):
        raise DashboardProvenanceError(detail="malformed_upstream_input_fingerprint")

    request_instant = _instant(as_of, field_name="as_of")
    seen_ids: set[str] = set()
    for record in briefing.records:
        _assert_upstream_briefing_record(record, as_of=request_instant)
        if record.score_record_id in seen_ids:
            raise DashboardIdentityError(
                detail=f"duplicate_score_record_id:{record.score_record_id}"
            )
        seen_ids.add(record.score_record_id)


def _assert_upstream_briefing_record(record: BriefingRecord, *, as_of: datetime) -> None:
    if not _is_sha256_hex(record.score_record_id):
        raise DashboardIdentityError(detail=f"malformed_score_record_id:{record.instrument_key}")
    record_instant = _instant(record.scoring_as_of, field_name="scoring_as_of")
    if record_instant != as_of:
        raise DashboardPitConflictError(
            detail=(
                "cross_as_of_record:"
                f"{record.instrument_key}:{record.scoring_as_of.isoformat()}:{as_of.isoformat()}"
            )
        )
    try:
        score = require_finite_decimal(record.score, field_name="score")
    except ValueError as exc:
        raise DashboardDomainError(detail=f"non_finite_score:{record.instrument_key}") from exc
    if not score.is_finite():
        raise DashboardDomainError(detail=f"non_finite_score:{record.instrument_key}")
    if score < Decimal("0") or score > Decimal("1"):
        raise DashboardDomainError(detail=f"score_out_of_domain:{record.instrument_key}")
    if not record.instrument_key:
        raise DashboardValidationError(detail="missing_instrument_key")


def _is_sha256_hex(value: str) -> bool:
    text = value.strip().lower()
    return len(text) == 64 and all(ch in "0123456789abcdef" for ch in text)
