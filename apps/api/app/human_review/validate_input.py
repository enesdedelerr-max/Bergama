"""Input Validation through Explicit Human Attestation Admission for Human Review."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.dashboard.models import DashboardPresentationOutput, DashboardPresentationRecord
from app.human_review.errors import (
    HumanReviewDomainError,
    HumanReviewHumanAuthorityError,
    HumanReviewIdentityError,
    HumanReviewPitConflictError,
    HumanReviewProvenanceError,
    HumanReviewUnauthorizedInputError,
    HumanReviewUnsupportedPolicyError,
    HumanReviewUpstreamPolicyError,
    HumanReviewValidationError,
)
from app.human_review.models import (
    HumanReviewConfig,
    HumanReviewRecordedAttestation,
    HumanReviewRequest,
)
from app.human_review.policy import (
    DIGEST_METHOD_V1,
    HISTORY_SPECIFICATION_V1,
    HUMAN_ATTESTATION_POLICY_V1,
    IDENTITY_SPECIFICATION_V1,
    ORDERING_PRESERVATION_POLICY_V1,
    POLICY_VERSION_V1,
    PRESENTATION_PRESERVATION_POLICY_V1,
    PROVENANCE_SPECIFICATION_V1,
    REQUIRED_UPSTREAM_DASHBOARD_IDENTITY_SPECIFICATION_ID,
    REQUIRED_UPSTREAM_DASHBOARD_POLICY_VERSION_ID,
    REQUIRED_UPSTREAM_DASHBOARD_PROVENANCE_SPECIFICATION_ID,
)
from app.market_data.money import require_finite_decimal
from app.market_data.timing import require_utc_aware


@dataclass(frozen=True, slots=True)
class ValidatedHumanReviewRequest:
    """Request admitted through stages 1–6 of the Human Review Pipeline."""

    dashboard: DashboardPresentationOutput
    as_of: datetime
    config: HumanReviewConfig
    attestation: HumanReviewRecordedAttestation


def validate_human_review_request(request: HumanReviewRequest) -> ValidatedHumanReviewRequest:
    """Admit only Governance Decision #2 / Policy Version v1-legal requests.

    Semantic stage order:
    1. Input Validation
    2. Policy Version Binding
    3. Configuration Binding
    4. PIT Validation
    5. Authorized Input Admission
    6. Explicit Human Attestation Admission
    """
    _assert_no_unauthorized_input(request)
    _assert_policy_and_configuration_binding(request.config)
    _assert_pit(request)
    _assert_authorized_dashboard(request.dashboard, as_of=request.as_of)
    _assert_explicit_human_attestation(request.attestation, dashboard=request.dashboard)
    return ValidatedHumanReviewRequest(
        dashboard=request.dashboard,
        as_of=request.as_of,
        config=request.config,
        attestation=request.attestation,
    )


def _assert_no_unauthorized_input(request: HumanReviewRequest) -> None:
    extra = getattr(request, "__pydantic_extra__", None)
    if extra:
        raise HumanReviewUnauthorizedInputError(detail=f"unexpected_extra_fields:{sorted(extra)}")


def _assert_policy_and_configuration_binding(config: HumanReviewConfig) -> None:
    if config.policy_version_id != POLICY_VERSION_V1:
        raise HumanReviewUnsupportedPolicyError(
            detail=f"unsupported_policy:{config.policy_version_id}"
        )
    if config.ordering_preservation_policy_id != ORDERING_PRESERVATION_POLICY_V1:
        raise HumanReviewUnsupportedPolicyError(
            detail=f"unsupported_ordering_preservation:{config.ordering_preservation_policy_id}"
        )
    if config.presentation_preservation_policy_id != PRESENTATION_PRESERVATION_POLICY_V1:
        raise HumanReviewUnsupportedPolicyError(
            detail=(
                "unsupported_presentation_preservation:"
                f"{config.presentation_preservation_policy_id}"
            )
        )
    if config.human_attestation_policy_id != HUMAN_ATTESTATION_POLICY_V1:
        raise HumanReviewUnsupportedPolicyError(
            detail=f"unsupported_human_attestation_policy:{config.human_attestation_policy_id}"
        )
    if config.identity_specification_id != IDENTITY_SPECIFICATION_V1:
        raise HumanReviewUnsupportedPolicyError(
            detail=f"unsupported_identity_specification:{config.identity_specification_id}"
        )
    if config.provenance_specification_id != PROVENANCE_SPECIFICATION_V1:
        raise HumanReviewUnsupportedPolicyError(
            detail=f"unsupported_provenance_specification:{config.provenance_specification_id}"
        )
    if config.history_specification_id != HISTORY_SPECIFICATION_V1:
        raise HumanReviewUnsupportedPolicyError(
            detail=f"unsupported_history_specification:{config.history_specification_id}"
        )
    if config.digest_method_id != DIGEST_METHOD_V1:
        raise HumanReviewUnsupportedPolicyError(
            detail=f"unsupported_digest_method:{config.digest_method_id}"
        )


def _instant(value: datetime, *, field_name: str) -> datetime:
    return require_utc_aware(value, field_name=field_name)


def _assert_pit(request: HumanReviewRequest) -> None:
    request_instant = _instant(request.as_of, field_name="as_of")
    dashboard_instant = _instant(request.dashboard.as_of, field_name="dashboard.as_of")
    if request_instant != dashboard_instant:
        raise HumanReviewPitConflictError(
            detail=(
                f"cross_as_of:{request.dashboard.as_of.isoformat()}:{request.as_of.isoformat()}"
            )
        )


def _assert_authorized_dashboard(
    dashboard: DashboardPresentationOutput,
    *,
    as_of: datetime,
) -> None:
    if dashboard.policy_version_id != REQUIRED_UPSTREAM_DASHBOARD_POLICY_VERSION_ID:
        raise HumanReviewUpstreamPolicyError(
            detail=f"upstream_dashboard_policy_mismatch:{dashboard.policy_version_id}"
        )
    if not _is_sha256_hex(dashboard.dashboard_output_id):
        raise HumanReviewIdentityError(detail="malformed_dashboard_output_id")
    provenance = dashboard.provenance
    if provenance.policy_version_id != REQUIRED_UPSTREAM_DASHBOARD_POLICY_VERSION_ID:
        raise HumanReviewUpstreamPolicyError(
            detail=f"upstream_dashboard_provenance_policy_mismatch:{provenance.policy_version_id}"
        )
    if provenance.identity_specification_id != (
        REQUIRED_UPSTREAM_DASHBOARD_IDENTITY_SPECIFICATION_ID
    ):
        raise HumanReviewProvenanceError(
            detail=(
                "upstream_dashboard_identity_specification_mismatch:"
                f"{provenance.identity_specification_id}"
            )
        )
    if provenance.provenance_specification_id != (
        REQUIRED_UPSTREAM_DASHBOARD_PROVENANCE_SPECIFICATION_ID
    ):
        raise HumanReviewProvenanceError(
            detail=(
                "upstream_dashboard_provenance_specification_mismatch:"
                f"{provenance.provenance_specification_id}"
            )
        )
    if not _is_sha256_hex(provenance.config_fingerprint):
        raise HumanReviewProvenanceError(detail="malformed_upstream_config_fingerprint")
    if not _is_sha256_hex(provenance.input_fingerprint):
        raise HumanReviewProvenanceError(detail="malformed_upstream_input_fingerprint")

    request_instant = _instant(as_of, field_name="as_of")
    seen_ids: set[str] = set()
    for record in dashboard.records:
        _assert_upstream_dashboard_record(record, as_of=request_instant)
        if record.score_record_id in seen_ids:
            raise HumanReviewIdentityError(
                detail=f"duplicate_score_record_id:{record.score_record_id}"
            )
        seen_ids.add(record.score_record_id)


def _assert_upstream_dashboard_record(
    record: DashboardPresentationRecord,
    *,
    as_of: datetime,
) -> None:
    if not _is_sha256_hex(record.score_record_id):
        raise HumanReviewIdentityError(detail=f"malformed_score_record_id:{record.instrument_key}")
    record_instant = _instant(record.scoring_as_of, field_name="scoring_as_of")
    if record_instant != as_of:
        raise HumanReviewPitConflictError(
            detail=(
                "cross_as_of_record:"
                f"{record.instrument_key}:{record.scoring_as_of.isoformat()}:{as_of.isoformat()}"
            )
        )
    try:
        score = require_finite_decimal(record.score, field_name="score")
    except ValueError as exc:
        raise HumanReviewDomainError(detail=f"non_finite_score:{record.instrument_key}") from exc
    if not score.is_finite():
        raise HumanReviewDomainError(detail=f"non_finite_score:{record.instrument_key}")
    if score < Decimal("0") or score > Decimal("1"):
        raise HumanReviewDomainError(detail=f"score_out_of_domain:{record.instrument_key}")
    if not record.instrument_key:
        raise HumanReviewValidationError(detail="missing_instrument_key")


def _assert_explicit_human_attestation(
    attestation: HumanReviewRecordedAttestation,
    *,
    dashboard: DashboardPresentationOutput,
) -> None:
    payload = attestation.recorded_payload
    if not payload.strip():
        raise HumanReviewHumanAuthorityError(detail="empty_recorded_attestation")
    forbidden_identities = {dashboard.dashboard_output_id}
    forbidden_identities.update(record.score_record_id for record in dashboard.records)
    if payload in forbidden_identities:
        raise HumanReviewHumanAuthorityError(detail="attestation_derived_from_dashboard")


def _is_sha256_hex(value: str) -> bool:
    text = value.strip().lower()
    return len(text) == 64 and all(ch in "0123456789abcdef" for ch in text)
