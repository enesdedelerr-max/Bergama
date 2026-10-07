"""Authoritative Intelligence Run snapshot contract and canonical equality (WS2).

Builds bounded public productization snapshots from completed ``PipelineResult``.
Does not expose ORM rows as the snapshot contract and does not define HTTP DTOs.
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.ai_decision_engine.models import AdeOutcomeKind, AdeResult
from app.dashboard.models import DashboardPresentationOutput
from app.human_review.models import HumanReviewOutput
from app.intelligence_pipeline.errors import sanitize_failure_detail
from app.intelligence_pipeline.models import PipelineOutcome, PipelineResult
from app.intelligence_pipeline.policy import (
    OUTCOME_ADMISSION_REJECTED,
    OUTCOME_COMPLETED_ADE_ABSTAIN,
    OUTCOME_COMPLETED_ADE_ACCEPT,
    OUTCOME_COMPLETED_DASHBOARD,
    OUTCOME_COMPLETED_HUMAN_REVIEW,
    OUTCOME_REQUIRED_STAGE_FAILED,
    STAGE_ADE,
    STAGE_BRIEFING,
    STAGE_CATALYST,
    STAGE_DASHBOARD,
    STAGE_GAP,
    STAGE_HUMAN_REVIEW,
    STAGE_SCORE,
    STAGE_WATCHLIST,
)
from app.intelligence_runs.constants import (
    FAILURE_DETAIL_MAX_CHARS,
    PERSISTED_OUTCOMES,
    SNAPSHOT_CONTRACT_VERSION,
)
from app.intelligence_runs.errors import (
    IntelligenceRunInvalidMaterializationError,
    IntelligenceRunInvalidPersistedRepresentationError,
)
from app.intelligence_runs.models import IntelligenceRunRecord
from app.market_data.timing import require_utc_aware

STAGE_KEYS: tuple[str, ...] = (
    STAGE_WATCHLIST,
    STAGE_GAP,
    STAGE_CATALYST,
    STAGE_SCORE,
    STAGE_BRIEFING,
    STAGE_DASHBOARD,
    STAGE_HUMAN_REVIEW,
    STAGE_ADE,
)

CORE_STAGES: tuple[str, ...] = (
    STAGE_WATCHLIST,
    STAGE_GAP,
    STAGE_CATALYST,
    STAGE_SCORE,
    STAGE_BRIEFING,
)

_STAGE_OUTPUT_ATTR: dict[str, str] = {
    STAGE_WATCHLIST: "watchlist",
    STAGE_GAP: "gaps",
    STAGE_CATALYST: "catalysts",
    STAGE_SCORE: "scores",
    STAGE_BRIEFING: "briefing",
    STAGE_DASHBOARD: "dashboard",
    STAGE_HUMAN_REVIEW: "human_review",
    STAGE_ADE: "ade",
}

_FORBIDDEN_ADE_PAYLOAD_KEY = "recorded_attestation_payload"


class StagePresenceStatus(StrEnum):
    """Frozen stage-presence status values."""

    NOT_EXECUTED = "NOT_EXECUTED"
    ABSENT = "ABSENT"
    EMPTY = "EMPTY"
    FAILED = "FAILED"
    PRESENT = "PRESENT"
    ABSTAINED = "ABSTAINED"


STAGE_STATUSES: tuple[str, ...] = tuple(member.value for member in StagePresenceStatus)


class AuthoritativeSnapshot(BaseModel):
    """Canonical authoritative productization snapshot (equality payload)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    pipeline_fingerprint: str | None = None
    snapshot_contract_version: str = Field(min_length=1)
    as_of: datetime | None = None
    outcome: str = Field(min_length=1)
    failed_stage: str | None = None
    failure_error_type: str | None = None
    failure_detail: str | None = None
    bindings: dict[str, Any] | None = None
    provenance: dict[str, Any]
    stage_presence: dict[str, str]
    dashboard_snapshot: dict[str, Any] | None = None
    human_review_snapshot: dict[str, Any] | None = None
    ade_snapshot: dict[str, Any] | None = None

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return require_utc_aware(value, field_name="as_of")

    @field_validator("outcome")
    @classmethod
    def require_frozen_outcome(cls, value: str) -> str:
        if value not in PERSISTED_OUTCOMES:
            msg = f"outcome must be one of {PERSISTED_OUTCOMES}"
            raise ValueError(msg)
        return value

    @field_validator("snapshot_contract_version")
    @classmethod
    def require_snapshot_version(cls, value: str) -> str:
        if value != SNAPSHOT_CONTRACT_VERSION:
            msg = f"snapshot_contract_version must be {SNAPSHOT_CONTRACT_VERSION!r}"
            raise ValueError(msg)
        return value

    @field_validator("failure_detail")
    @classmethod
    def require_bounded_failure_detail(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if len(value) > FAILURE_DETAIL_MAX_CHARS:
            msg = f"failure_detail exceeds {FAILURE_DETAIL_MAX_CHARS} characters"
            raise ValueError(msg)
        return value

    @field_validator("stage_presence")
    @classmethod
    def require_exact_stage_keys(cls, value: dict[str, str]) -> dict[str, str]:
        if tuple(value.keys()) != STAGE_KEYS and set(value.keys()) != set(STAGE_KEYS):
            msg = f"stage_presence must contain exactly keys {STAGE_KEYS}"
            raise ValueError(msg)
        ordered = {key: value[key] for key in STAGE_KEYS}
        for key, status in ordered.items():
            if status not in STAGE_STATUSES:
                msg = f"invalid stage presence status for {key}: {status}"
                raise ValueError(msg)
        return ordered


def canonical_snapshot_json(snapshot: AuthoritativeSnapshot) -> str:
    """Deterministic canonical JSON for authoritative snapshot equality."""
    payload = snapshot.model_dump(mode="json")
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_snapshots_equal(left: AuthoritativeSnapshot, right: AuthoritativeSnapshot) -> bool:
    """Compare two authoritative snapshots via deterministic canonical JSON."""
    return canonical_snapshot_json(left) == canonical_snapshot_json(right)


def enforce_dashboard_invariant(snapshot: AuthoritativeSnapshot) -> None:
    """Require dashboard snapshot non-null IFF stage_presence.dashboard == PRESENT."""
    dashboard_status = snapshot.stage_presence[STAGE_DASHBOARD]
    has_snapshot = snapshot.dashboard_snapshot is not None
    if dashboard_status == StagePresenceStatus.PRESENT.value and not has_snapshot:
        raise IntelligenceRunInvalidMaterializationError(
            detail="dashboard PRESENT requires non-null dashboard snapshot",
        )
    if dashboard_status != StagePresenceStatus.PRESENT.value and has_snapshot:
        raise IntelligenceRunInvalidMaterializationError(
            detail=(
                "non-null dashboard snapshot is only allowed when "
                "stage_presence.dashboard == PRESENT"
            ),
        )


def build_ade_product_snapshot(ade: AdeResult) -> dict[str, Any]:
    """Serialize ADE public product snapshot without recorded attestation payload."""
    data = ade.model_dump(mode="json")
    provenance = data.get("provenance")
    if isinstance(provenance, dict):
        provenance.pop(_FORBIDDEN_ADE_PAYLOAD_KEY, None)
    _assert_no_forbidden_ade_payload(data)
    return data


def build_authoritative_snapshot(result: PipelineResult) -> AuthoritativeSnapshot:
    """Validate ``PipelineResult`` and build the authoritative equality snapshot."""
    if not isinstance(result, PipelineResult):
        raise IntelligenceRunInvalidMaterializationError(
            detail="materialization input must be a PipelineResult",
        )

    outcome = (
        result.outcome.value if isinstance(result.outcome, PipelineOutcome) else str(result.outcome)
    )
    if outcome not in PERSISTED_OUTCOMES:
        raise IntelligenceRunInvalidMaterializationError(
            detail=f"unsupported PipelineOutcome: {outcome}",
        )

    failure_detail = sanitize_failure_detail(result.failure_detail)
    if failure_detail is not None and len(failure_detail) > FAILURE_DETAIL_MAX_CHARS:
        failure_detail = failure_detail[:FAILURE_DETAIL_MAX_CHARS]

    stage_presence = build_stage_presence(result)
    dashboard_snapshot = (
        result.dashboard.model_dump(mode="json") if result.dashboard is not None else None
    )
    human_review_snapshot = (
        result.human_review.model_dump(mode="json") if result.human_review is not None else None
    )
    ade_snapshot = build_ade_product_snapshot(result.ade) if result.ade is not None else None

    fingerprint = result.provenance.pipeline_fingerprint
    bindings = result.bindings.model_dump(mode="json") if result.bindings is not None else None
    provenance = result.provenance.model_dump(mode="json")

    _validate_outcome_structure(
        outcome=outcome,
        result=result,
        fingerprint=fingerprint,
        bindings=bindings,
        stage_presence=stage_presence,
        dashboard_snapshot=dashboard_snapshot,
        human_review_snapshot=human_review_snapshot,
        ade_snapshot=ade_snapshot,
        failure_detail=failure_detail,
    )

    snapshot = AuthoritativeSnapshot(
        pipeline_fingerprint=fingerprint,
        snapshot_contract_version=SNAPSHOT_CONTRACT_VERSION,
        as_of=result.as_of,
        outcome=outcome,
        failed_stage=result.failed_stage,
        failure_error_type=result.failure_error_type,
        failure_detail=failure_detail,
        bindings=bindings,
        provenance=provenance,
        stage_presence=stage_presence,
        dashboard_snapshot=dashboard_snapshot,
        human_review_snapshot=human_review_snapshot,
        ade_snapshot=ade_snapshot,
    )
    enforce_dashboard_invariant(snapshot)
    _assert_no_forbidden_ade_payload(snapshot.model_dump(mode="json"))
    return snapshot


def reconstruct_authoritative_snapshot(record: IntelligenceRunRecord) -> AuthoritativeSnapshot:
    """Rebuild authoritative equality content from a persisted ORM row."""
    if not isinstance(record, IntelligenceRunRecord):
        raise IntelligenceRunInvalidPersistedRepresentationError(
            detail="record must be an IntelligenceRunRecord",
        )
    try:
        stage_presence = record.stage_presence_json
        if not isinstance(stage_presence, dict):
            raise TypeError("stage_presence_json must be an object")
        provenance = record.provenance_json
        if not isinstance(provenance, dict):
            raise TypeError("provenance_json must be an object")
        snapshot = AuthoritativeSnapshot(
            pipeline_fingerprint=record.pipeline_fingerprint,
            snapshot_contract_version=record.snapshot_contract_version,
            as_of=record.as_of,
            outcome=record.outcome,
            failed_stage=record.failed_stage,
            failure_error_type=record.failure_error_type,
            failure_detail=record.failure_detail,
            bindings=record.bindings_json,
            provenance=provenance,
            stage_presence={str(k): str(v) for k, v in stage_presence.items()},
            dashboard_snapshot=record.dashboard_snapshot_json,
            human_review_snapshot=record.human_review_snapshot_json,
            ade_snapshot=record.ade_snapshot_json,
        )
        enforce_dashboard_invariant(snapshot)
        _assert_no_forbidden_ade_payload(snapshot.model_dump(mode="json"))
    except (
        TypeError,
        ValueError,
        IntelligenceRunInvalidMaterializationError,
    ) as exc:
        raise IntelligenceRunInvalidPersistedRepresentationError(
            detail="corrupt or incomplete persisted authoritative snapshot",
        ) from exc
    return snapshot


def build_stage_presence(result: PipelineResult) -> dict[str, str]:
    """Derive the frozen 8-key stage presence map from completed PipelineResult."""
    outcome = result.outcome.value
    executed = set(result.provenance.executed_stages)
    failed_stage = result.failed_stage

    if outcome == OUTCOME_ADMISSION_REJECTED:
        return {
            STAGE_WATCHLIST: StagePresenceStatus.NOT_EXECUTED.value,
            STAGE_GAP: StagePresenceStatus.NOT_EXECUTED.value,
            STAGE_CATALYST: StagePresenceStatus.NOT_EXECUTED.value,
            STAGE_SCORE: StagePresenceStatus.NOT_EXECUTED.value,
            STAGE_BRIEFING: StagePresenceStatus.NOT_EXECUTED.value,
            STAGE_DASHBOARD: StagePresenceStatus.ABSENT.value,
            STAGE_HUMAN_REVIEW: StagePresenceStatus.ABSENT.value,
            STAGE_ADE: StagePresenceStatus.ABSENT.value,
        }

    presence: dict[str, str] = {}
    for stage in (*CORE_STAGES, STAGE_DASHBOARD):
        presence[stage] = _status_for_executed_stage(
            stage=stage,
            result=result,
            executed=executed,
            failed_stage=failed_stage,
        )

    if result.human_review is not None:
        if not isinstance(result.human_review, HumanReviewOutput):
            raise IntelligenceRunInvalidMaterializationError(
                detail="human_review must be HumanReviewOutput when present",
            )
        presence[STAGE_HUMAN_REVIEW] = StagePresenceStatus.PRESENT.value
    elif STAGE_HUMAN_REVIEW in executed:
        raise IntelligenceRunInvalidMaterializationError(
            detail="human_review executed without HumanReviewOutput",
        )
    else:
        presence[STAGE_HUMAN_REVIEW] = StagePresenceStatus.ABSENT.value

    if result.ade is not None:
        if not isinstance(result.ade, AdeResult):
            raise IntelligenceRunInvalidMaterializationError(
                detail="ade must be AdeResult when present",
            )
        if result.ade.outcome_kind is AdeOutcomeKind.EXPLICIT_ABSTENTION:
            presence[STAGE_ADE] = StagePresenceStatus.ABSTAINED.value
        elif result.ade.outcome_kind is AdeOutcomeKind.AUTHORITATIVE_DECISION:
            presence[STAGE_ADE] = StagePresenceStatus.PRESENT.value
        else:
            raise IntelligenceRunInvalidMaterializationError(
                detail=f"unsupported ADE outcome_kind: {result.ade.outcome_kind}",
            )
    elif STAGE_ADE in executed:
        raise IntelligenceRunInvalidMaterializationError(
            detail="ade executed without AdeResult",
        )
    else:
        presence[STAGE_ADE] = StagePresenceStatus.ABSENT.value

    return {key: presence[key] for key in STAGE_KEYS}


def _status_for_executed_stage(
    *,
    stage: str,
    result: PipelineResult,
    executed: set[str],
    failed_stage: str | None,
) -> str:
    attr = _STAGE_OUTPUT_ATTR[stage]
    output = getattr(result, attr)
    if failed_stage == stage:
        return StagePresenceStatus.FAILED.value
    if stage not in executed:
        return StagePresenceStatus.NOT_EXECUTED.value
    if output is None:
        raise IntelligenceRunInvalidMaterializationError(
            detail=f"stage {stage} executed without public output",
        )
    if stage == STAGE_DASHBOARD:
        if not isinstance(output, DashboardPresentationOutput):
            raise IntelligenceRunInvalidMaterializationError(
                detail="dashboard output must be DashboardPresentationOutput",
            )
        if len(output.records) == 0:
            return StagePresenceStatus.EMPTY.value
        return StagePresenceStatus.PRESENT.value
    if _is_empty_collection(output):
        return StagePresenceStatus.EMPTY.value
    return StagePresenceStatus.PRESENT.value


def _is_empty_collection(output: object) -> bool:
    entries = getattr(output, "entries", None)
    if isinstance(entries, tuple):
        return len(entries) == 0
    records = getattr(output, "records", None)
    if isinstance(records, tuple):
        return len(records) == 0
    return False


def _validate_outcome_structure(
    *,
    outcome: str,
    result: PipelineResult,
    fingerprint: str | None,
    bindings: dict[str, Any] | None,
    stage_presence: dict[str, str],
    dashboard_snapshot: dict[str, Any] | None,
    human_review_snapshot: dict[str, Any] | None,
    ade_snapshot: dict[str, Any] | None,
    failure_detail: str | None,
) -> None:
    dashboard_status = stage_presence[STAGE_DASHBOARD]
    hr_status = stage_presence[STAGE_HUMAN_REVIEW]
    ade_status = stage_presence[STAGE_ADE]

    if outcome == OUTCOME_ADMISSION_REJECTED:
        if result.as_of is not None or fingerprint is not None or bindings is not None:
            raise IntelligenceRunInvalidMaterializationError(
                detail="admission_rejected requires null as_of, fingerprint, and bindings",
            )
        if any(
            getattr(result, attr) is not None
            for attr in (
                "watchlist",
                "gaps",
                "catalysts",
                "scores",
                "briefing",
                "dashboard",
                "human_review",
                "ade",
            )
        ):
            raise IntelligenceRunInvalidMaterializationError(
                detail="admission_rejected must not carry stage outputs",
            )
        has_product_snapshot = (
            dashboard_snapshot is not None
            or human_review_snapshot is not None
            or ade_snapshot is not None
        )
        if has_product_snapshot:
            raise IntelligenceRunInvalidMaterializationError(
                detail="admission_rejected must not carry product snapshots",
            )
        return

    if result.as_of is None or fingerprint is None or bindings is None:
        raise IntelligenceRunInvalidMaterializationError(
            detail="admitted outcomes require as_of, pipeline_fingerprint, and bindings",
        )
    if len(fingerprint) != 64 or any(ch not in "0123456789abcdef" for ch in fingerprint):
        raise IntelligenceRunInvalidMaterializationError(
            detail="pipeline_fingerprint must be 64-char lowercase hex",
        )

    if outcome == OUTCOME_REQUIRED_STAGE_FAILED:
        if result.failed_stage is None or result.failure_error_type is None:
            raise IntelligenceRunInvalidMaterializationError(
                detail="required_stage_failed requires failed_stage and failure_error_type",
            )
        if failure_detail is None:
            raise IntelligenceRunInvalidMaterializationError(
                detail="required_stage_failed requires bounded failure_detail",
            )
        return

    has_failure_metadata = (
        result.failed_stage is not None
        or result.failure_error_type is not None
        or failure_detail is not None
    )
    if has_failure_metadata:
        raise IntelligenceRunInvalidMaterializationError(
            detail="completed outcomes must not carry failure metadata",
        )

    if dashboard_status != StagePresenceStatus.PRESENT.value or dashboard_snapshot is None:
        raise IntelligenceRunInvalidMaterializationError(
            detail=f"{outcome} requires dashboard PRESENT with snapshot",
        )

    if outcome == OUTCOME_COMPLETED_DASHBOARD:
        if hr_status != StagePresenceStatus.ABSENT.value or human_review_snapshot is not None:
            raise IntelligenceRunInvalidMaterializationError(
                detail="completed_dashboard requires human_review ABSENT",
            )
        if ade_status != StagePresenceStatus.ABSENT.value or ade_snapshot is not None:
            raise IntelligenceRunInvalidMaterializationError(
                detail="completed_dashboard requires ade ABSENT",
            )
        return

    if outcome == OUTCOME_COMPLETED_HUMAN_REVIEW:
        if hr_status != StagePresenceStatus.PRESENT.value or human_review_snapshot is None:
            raise IntelligenceRunInvalidMaterializationError(
                detail="completed_human_review requires human_review PRESENT with snapshot",
            )
        if ade_status != StagePresenceStatus.ABSENT.value or ade_snapshot is not None:
            raise IntelligenceRunInvalidMaterializationError(
                detail="completed_human_review requires ade ABSENT",
            )
        return

    if outcome == OUTCOME_COMPLETED_ADE_ACCEPT:
        if hr_status != StagePresenceStatus.PRESENT.value or human_review_snapshot is None:
            raise IntelligenceRunInvalidMaterializationError(
                detail="completed_ade_accept requires human_review PRESENT with snapshot",
            )
        if ade_status != StagePresenceStatus.PRESENT.value or ade_snapshot is None:
            raise IntelligenceRunInvalidMaterializationError(
                detail="completed_ade_accept requires ade PRESENT with snapshot",
            )
        return

    if outcome == OUTCOME_COMPLETED_ADE_ABSTAIN:
        if hr_status != StagePresenceStatus.PRESENT.value or human_review_snapshot is None:
            raise IntelligenceRunInvalidMaterializationError(
                detail="completed_ade_abstain requires human_review PRESENT with snapshot",
            )
        if ade_status != StagePresenceStatus.ABSTAINED.value or ade_snapshot is None:
            raise IntelligenceRunInvalidMaterializationError(
                detail="completed_ade_abstain requires ade ABSTAINED with snapshot",
            )
        return

    raise IntelligenceRunInvalidMaterializationError(detail=f"unhandled outcome: {outcome}")


def _assert_no_forbidden_ade_payload(payload: object) -> None:
    """Fail closed if ADE recorded attestation payload appears anywhere."""
    if isinstance(payload, dict):
        if _FORBIDDEN_ADE_PAYLOAD_KEY in payload:
            raise IntelligenceRunInvalidMaterializationError(
                detail="ADE recorded_attestation_payload is forbidden in product snapshot",
            )
        for value in payload.values():
            _assert_no_forbidden_ade_payload(value)
    elif isinstance(payload, list | tuple):
        for item in payload:
            _assert_no_forbidden_ade_payload(item)
