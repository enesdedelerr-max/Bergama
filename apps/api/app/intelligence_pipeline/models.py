"""Immutable Intelligence Pipeline Issue #126/#128 contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.ai_decision_engine.models import AdeConfig, AdeOutcomeKind, AdeResult
from app.core.premarket_settings import PremarketSettings
from app.dashboard.models import DashboardConfig, DashboardPresentationOutput
from app.human_review.models import (
    HumanReviewConfig,
    HumanReviewOutput,
    HumanReviewRecordedAttestation,
)
from app.intelligence_pipeline.policy import (
    GLOBAL_OUTCOME_FAMILIES,
    ISSUE_1_REACHABLE_OUTCOMES,
    OUTCOME_ADMISSION_REJECTED,
    OUTCOME_COMPLETED_ADE_ABSTAIN,
    OUTCOME_COMPLETED_ADE_ACCEPT,
    OUTCOME_COMPLETED_DASHBOARD,
    OUTCOME_COMPLETED_HUMAN_REVIEW,
    OUTCOME_REQUIRED_STAGE_FAILED,
    POLICY_VERSION_V1,
)
from app.market_data.events.bar import BarEvent
from app.market_data.events.news import NewsEvent
from app.market_data.timing import require_utc_aware
from app.premarket.catalyst.models import CatalystCollection, CatalystConfig
from app.premarket.gap.models import GapCollection, GapConfig
from app.premarket.morning_briefing.models import BriefingCollection, BriefingConfig
from app.premarket.scoring.models import ScoreCollection, ScoreConfig
from app.premarket.watchlist.models import (
    Watchlist,
    WatchlistCandidate,
    WatchlistConfig,
)


class PipelineOutcome(StrEnum):
    """Global composition outcome family identities (Policy PD-13-03)."""

    ADMISSION_REJECTED = OUTCOME_ADMISSION_REJECTED
    REQUIRED_STAGE_FAILED = OUTCOME_REQUIRED_STAGE_FAILED
    COMPLETED_DASHBOARD = OUTCOME_COMPLETED_DASHBOARD
    COMPLETED_HUMAN_REVIEW = OUTCOME_COMPLETED_HUMAN_REVIEW
    COMPLETED_ADE_ACCEPT = OUTCOME_COMPLETED_ADE_ACCEPT
    COMPLETED_ADE_ABSTAIN = OUTCOME_COMPLETED_ADE_ABSTAIN


assert tuple(member.value for member in PipelineOutcome) == GLOBAL_OUTCOME_FAMILIES
assert (
    PipelineOutcome.ADMISSION_REJECTED.value,
    PipelineOutcome.REQUIRED_STAGE_FAILED.value,
    PipelineOutcome.COMPLETED_DASHBOARD.value,
) == ISSUE_1_REACHABLE_OUTCOMES


class PipelineBindings(BaseModel):
    """Governed stage Policy/config bindings pinned at admission."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_version_id: str = Field(default=POLICY_VERSION_V1, min_length=1, max_length=128)
    watchlist_ordering_policy_id: str = Field(min_length=1, max_length=128)
    gap_selection_policy_id: str = Field(min_length=1, max_length=128)
    gap_ordering_policy_id: str = Field(min_length=1, max_length=128)
    catalyst_ordering_policy_id: str = Field(min_length=1, max_length=128)
    score_policy_version_id: str = Field(min_length=1, max_length=128)
    score_weight_profile_id: str = Field(min_length=1, max_length=128)
    briefing_policy_version_id: str = Field(min_length=1, max_length=128)
    dashboard_policy_version_id: str = Field(min_length=1, max_length=128)
    human_review_policy_version_id: str | None = Field(default=None, min_length=1, max_length=128)
    ade_policy_version_id: str | None = Field(default=None, min_length=1, max_length=128)


class PipelineProvenance(BaseModel):
    """Thin composition provenance (no stage provenance rewrite; no replay identity)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    as_of: datetime | None = None
    stage_order: tuple[str, ...] = ()
    executed_stages: tuple[str, ...] = ()
    watchlist_config_fingerprint: str | None = None
    watchlist_input_fingerprint: str | None = None
    gap_config_fingerprint: str | None = None
    gap_input_fingerprint: str | None = None
    catalyst_config_fingerprint: str | None = None
    catalyst_input_fingerprint: str | None = None
    score_config_fingerprint: str | None = None
    score_input_fingerprint: str | None = None
    briefing_config_fingerprint: str | None = None
    briefing_input_fingerprint: str | None = None
    dashboard_config_fingerprint: str | None = None
    dashboard_input_fingerprint: str | None = None
    human_review_output_id: str | None = None
    human_review_config_fingerprint: str | None = None
    human_review_input_fingerprint: str | None = None
    recorded_attestation_fingerprint: str | None = None
    ade_decision_id: str | None = None
    ade_outcome_kind: AdeOutcomeKind | None = None
    ade_evidence_fingerprint: str | None = None
    outcome: PipelineOutcome | None = None
    failed_stage: str | None = None

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return require_utc_aware(value, field_name="as_of")


class PipelineRequest(BaseModel):
    """Bounded typed Pipeline admission request for Issue #126/#128 composition."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    as_of: datetime
    candidates: tuple[WatchlistCandidate, ...]
    watchlist_config: WatchlistConfig
    bars: tuple[BarEvent, ...]
    gap_config: GapConfig = Field(default_factory=GapConfig)
    events: tuple[NewsEvent, ...]
    catalyst_config: CatalystConfig
    score_config: ScoreConfig = Field(default_factory=ScoreConfig)
    briefing_config: BriefingConfig = Field(default_factory=BriefingConfig)
    dashboard_config: DashboardConfig = Field(default_factory=DashboardConfig)
    settings: PremarketSettings | None = None
    hr_requested: bool = False
    hr_attestation: HumanReviewRecordedAttestation | None = None
    hr_config: HumanReviewConfig | None = None
    ade_requested: bool = False
    ade_config: AdeConfig | None = None

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime) -> datetime:
        return require_utc_aware(value, field_name="as_of")


class PipelineResult(BaseModel):
    """Bounded typed Pipeline composition result for Issue #126/#128."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: PipelineOutcome
    as_of: datetime | None = None
    bindings: PipelineBindings | None = None
    provenance: PipelineProvenance
    watchlist: Watchlist | None = None
    gaps: GapCollection | None = None
    catalysts: CatalystCollection | None = None
    scores: ScoreCollection | None = None
    briefing: BriefingCollection | None = None
    dashboard: DashboardPresentationOutput | None = None
    human_review: HumanReviewOutput | None = None
    ade: AdeResult | None = None
    failed_stage: str | None = None
    failure_detail: str | None = None
    failure_error_type: str | None = None

    @field_validator("as_of")
    @classmethod
    def require_utc_as_of(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return require_utc_aware(value, field_name="as_of")
