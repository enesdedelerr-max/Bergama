"""Immutable Premarket Analyst Projection Core contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.dashboard.models import DashboardPresentationOutput
from app.market_data.timing import require_utc_aware
from app.premarket.catalyst.models import CatalystCollection
from app.premarket.gap.models import GapCollection
from app.premarket.morning_briefing import BriefingCollection
from app.premarket.scoring.models import ScoreCollection
from app.premarket.watchlist.models import Watchlist
from app.premarket_analyst.policy import (
    ANALYST_DEFINITION_VERSION_V1,
    DIGEST_METHOD_V1,
    IDENTITY_SPECIFICATION_V1,
    ORDERING_POLICY_V1,
    POLICY_VERSION_V1,
    PROVENANCE_SPECIFICATION_V1,
    RISK_FLAG_CATEGORIES,
)

EvaluationState = Literal[
    "EVALUABLE",
    "INSUFFICIENT_EVIDENCE",
    "NOT_EVALUABLE",
    "ABSTAIN",
]

RiskFlagCategory = Literal[
    "MISSING_DATA",
    "STALE_DATA",
    "CONFLICTING_EVIDENCE",
    "WEAK_CATALYST_COVERAGE",
    "FRESHNESS_CONCERN",
    "STAGE_FAILURE_PRESENT",
    "UNSUPPORTED_EVALUATION",
    "NOT_EVALUABLE_INPUT",
]


class AnalystConfig(BaseModel):
    """Pinned Premarket Analyst projection configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    analyst_definition_version: str = Field(
        default=ANALYST_DEFINITION_VERSION_V1,
        min_length=1,
        max_length=128,
    )
    policy_version_id: str = Field(default=POLICY_VERSION_V1, min_length=1, max_length=128)
    identity_specification_id: str = Field(
        default=IDENTITY_SPECIFICATION_V1,
        min_length=1,
        max_length=128,
    )
    provenance_specification_id: str = Field(
        default=PROVENANCE_SPECIFICATION_V1,
        min_length=1,
        max_length=128,
    )
    digest_method_id: str = Field(default=DIGEST_METHOD_V1, min_length=1, max_length=128)
    ordering_policy_id: str = Field(default=ORDERING_POLICY_V1, min_length=1, max_length=128)

    @field_validator("analyst_definition_version")
    @classmethod
    def validate_definition(cls, value: str) -> str:
        text = value.strip()
        if text != ANALYST_DEFINITION_VERSION_V1:
            msg = f"unsupported analyst_definition_version: {text}"
            raise ValueError(msg)
        return text

    @field_validator("policy_version_id")
    @classmethod
    def validate_policy(cls, value: str) -> str:
        text = value.strip()
        if text != POLICY_VERSION_V1:
            msg = f"unsupported policy_version_id: {text}"
            raise ValueError(msg)
        return text

    @field_validator("identity_specification_id")
    @classmethod
    def validate_identity(cls, value: str) -> str:
        text = value.strip()
        if text != IDENTITY_SPECIFICATION_V1:
            msg = f"unsupported identity_specification_id: {text}"
            raise ValueError(msg)
        return text

    @field_validator("provenance_specification_id")
    @classmethod
    def validate_provenance(cls, value: str) -> str:
        text = value.strip()
        if text != PROVENANCE_SPECIFICATION_V1:
            msg = f"unsupported provenance_specification_id: {text}"
            raise ValueError(msg)
        return text

    @field_validator("digest_method_id")
    @classmethod
    def validate_digest(cls, value: str) -> str:
        text = value.strip()
        if text != DIGEST_METHOD_V1:
            msg = f"unsupported digest_method_id: {text}"
            raise ValueError(msg)
        return text

    @field_validator("ordering_policy_id")
    @classmethod
    def validate_ordering(cls, value: str) -> str:
        text = value.strip()
        if text != ORDERING_POLICY_V1:
            msg = f"unsupported ordering_policy_id: {text}"
            raise ValueError(msg)
        return text


class AnalystProjectionRequest(BaseModel):
    """Pure projection request over already-produced upstream public outputs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    as_of: datetime
    watchlist: Watchlist
    config: AnalystConfig = Field(default_factory=AnalystConfig)
    gaps: GapCollection | None = None
    catalysts: CatalystCollection | None = None
    scores: ScoreCollection | None = None
    briefing: BriefingCollection | None = None
    dashboard: DashboardPresentationOutput | None = None
    membership_complete: bool = True
    upstream_pipeline_failure_identity: str | None = Field(default=None, max_length=256)
    unsupported_instrument_keys: tuple[str, ...] = ()

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")

    @field_validator("upstream_pipeline_failure_identity")
    @classmethod
    def strip_failure_identity(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        return text or None

    @field_validator("unsupported_instrument_keys")
    @classmethod
    def normalize_unsupported(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized: list[str] = []
        seen: set[str] = set()
        for raw in value:
            key = raw.strip()
            if not key:
                msg = "unsupported_instrument_keys must not contain empty keys"
                raise ValueError(msg)
            if key in seen:
                msg = f"duplicate unsupported_instrument_key: {key}"
                raise ValueError(msg)
            seen.add(key)
            normalized.append(key)
        return tuple(normalized)


class GapCoverageAggregates(BaseModel):
    """Deterministic gap coverage aggregates from GapCollection only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    record_count: int = Field(ge=0)
    instrument_count: int = Field(ge=0)
    direction_up_count: int = Field(ge=0)
    direction_down_count: int = Field(ge=0)
    direction_flat_count: int = Field(ge=0)
    gap_record_ids: tuple[str, ...] = ()


class CatalystCoverageAggregates(BaseModel):
    """Deterministic catalyst coverage aggregates."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    record_count: int = Field(ge=0)
    linked_instrument_count: int = Field(ge=0)
    catalyst_record_ids: tuple[str, ...] = ()
    absence_marker: bool


class ScoreDashboardRefs(BaseModel):
    """Score / dashboard identity references only (no recomputation)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    score_record_ids: tuple[str, ...] = ()
    score_collection_input_fingerprint: str | None = Field(default=None, max_length=64)
    dashboard_output_id: str | None = Field(default=None, max_length=64)
    briefing_id: str | None = Field(default=None, max_length=64)


class DataCompletenessMarkers(BaseModel):
    """Explicit completeness markers for market summary."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    watchlist_present: bool
    gaps_present: bool
    catalysts_present: bool
    scores_present: bool
    dashboard_present: bool
    briefing_present: bool
    membership_complete: bool


class MarketSummary(BaseModel):
    """Structured Market Summary projection."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    as_of: datetime
    watchlist_count: int = Field(ge=0)
    watchlist_membership_refs: tuple[str, ...]
    gap_coverage: GapCoverageAggregates
    catalyst_coverage: CatalystCoverageAggregates
    score_dashboard_refs: ScoreDashboardRefs
    completeness: DataCompletenessMarkers

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")


class CatalystSummaryRecord(BaseModel):
    """CatalystRecord-derived summary leaf (no generative prose)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    catalyst_record_id: str = Field(min_length=64, max_length=64)
    instrument_key: str | None = Field(default=None, max_length=128)
    catalyst_type: str = Field(min_length=1, max_length=64)
    event_time: datetime
    known_at: datetime
    as_of: datetime
    source_provider: str = Field(min_length=1, max_length=64)
    source_event_id: str | None = Field(default=None, max_length=256)
    source_content_fingerprint: str = Field(min_length=64, max_length=64)
    rule_id: str = Field(min_length=1, max_length=128)

    @field_validator("event_time", "known_at", "as_of")
    @classmethod
    def require_utc(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="timestamp")


class CatalystSummary(BaseModel):
    """Structured Catalyst Summary projection."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    as_of: datetime
    records: tuple[CatalystSummaryRecord, ...]
    absence_marker: bool
    unavailable_marker: bool

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")


class StructuredThesis(BaseModel):
    """Narrow structured thesis (informational only)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    thesis_id: str = Field(min_length=64, max_length=64)
    instrument_key: str = Field(min_length=1, max_length=128)
    as_of: datetime
    supporting_evidence_refs: tuple[str, ...]
    counter_evidence_refs: tuple[str, ...]
    observed_conditions: tuple[str, ...]
    informational_invalidation_conditions: tuple[str, ...]
    uncertainty_markers: tuple[str, ...]
    evaluation_state: EvaluationState
    provenance_refs: tuple[str, ...]

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")


class RiskFlag(BaseModel):
    """Descriptive risk flag without enforcement or severity taxonomy."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    risk_flag_id: str = Field(min_length=64, max_length=64)
    category: RiskFlagCategory
    evidence_refs: tuple[str, ...]
    as_of: datetime
    provenance_refs: tuple[str, ...]

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        if value not in RISK_FLAG_CATEGORIES:
            msg = f"unsupported risk flag category: {value}"
            raise ValueError(msg)
        return value

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")


class AnalystProvenance(BaseModel):
    """Replay-relevant analyst provenance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    analyst_definition_version: str = Field(min_length=1, max_length=128)
    policy_version_id: str = Field(min_length=1, max_length=128)
    identity_specification_id: str = Field(min_length=1, max_length=128)
    provenance_specification_id: str = Field(min_length=1, max_length=128)
    digest_method_id: str = Field(min_length=1, max_length=128)
    ordering_policy_id: str = Field(min_length=1, max_length=128)
    as_of: datetime
    config_fingerprint: str = Field(min_length=64, max_length=64)
    input_fingerprint: str = Field(min_length=64, max_length=64)
    upstream_fingerprints: tuple[str, ...] = ()
    upstream_pipeline_failure_identity: str | None = Field(default=None, max_length=256)
    source_identifiers: tuple[str, ...] = ()

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")

    @field_validator("config_fingerprint", "input_fingerprint")
    @classmethod
    def require_sha256_hex(cls, value: str) -> str:
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "fingerprint must be sha256 hex"
            raise ValueError(msg)
        return text


class PremarketAnalystArtifact(BaseModel):
    """Typed Premarket Analyst projection artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    analyst_artifact_id: str = Field(min_length=64, max_length=64)
    analyst_definition_version: str = Field(min_length=1, max_length=128)
    as_of: datetime
    evaluation_state: EvaluationState
    market_summary: MarketSummary
    catalyst_summary: CatalystSummary
    theses: tuple[StructuredThesis, ...]
    risk_flags: tuple[RiskFlag, ...]
    provenance: AnalystProvenance

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")

    @field_validator("analyst_artifact_id")
    @classmethod
    def require_sha256_hex(cls, value: str) -> str:
        text = value.strip().lower()
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            msg = "analyst_artifact_id must be sha256 hex"
            raise ValueError(msg)
        return text

    @model_validator(mode="after")
    def require_matching_as_of(self) -> Self:
        if self.market_summary.as_of != self.as_of:
            msg = "market_summary.as_of mismatch"
            raise ValueError(msg)
        if self.catalyst_summary.as_of != self.as_of:
            msg = "catalyst_summary.as_of mismatch"
            raise ValueError(msg)
        if self.provenance.as_of != self.as_of:
            msg = "provenance.as_of mismatch"
            raise ValueError(msg)
        return self
