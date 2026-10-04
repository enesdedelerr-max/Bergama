"""Intelligence Pipeline Policy Version v1 composition constants."""

from __future__ import annotations

POLICY_VERSION_V1 = "intelligence-pipeline.policy.v1"
IMPLEMENTATION_AUTHORIZATION_ID = "intelligence-pipeline.implementation-authorization.v1"

# Global composition outcome family identities (Policy PD-13-03).
OUTCOME_ADMISSION_REJECTED = "admission_rejected"
OUTCOME_REQUIRED_STAGE_FAILED = "required_stage_failed"
OUTCOME_COMPLETED_DASHBOARD = "completed_dashboard"
OUTCOME_COMPLETED_HUMAN_REVIEW = "completed_human_review"
OUTCOME_COMPLETED_ADE_ACCEPT = "completed_ade_accept"
OUTCOME_COMPLETED_ADE_ABSTAIN = "completed_ade_abstain"

GLOBAL_OUTCOME_FAMILIES: tuple[str, ...] = (
    OUTCOME_ADMISSION_REJECTED,
    OUTCOME_REQUIRED_STAGE_FAILED,
    OUTCOME_COMPLETED_DASHBOARD,
    OUTCOME_COMPLETED_HUMAN_REVIEW,
    OUTCOME_COMPLETED_ADE_ACCEPT,
    OUTCOME_COMPLETED_ADE_ABSTAIN,
)

# Issue #126 reachable subset (HR/ADE terminals deferred to Future Issue 2).
ISSUE_1_REACHABLE_OUTCOMES: tuple[str, ...] = (
    OUTCOME_ADMISSION_REJECTED,
    OUTCOME_REQUIRED_STAGE_FAILED,
    OUTCOME_COMPLETED_DASHBOARD,
)

STAGE_WATCHLIST = "watchlist"
STAGE_GAP = "gap"
STAGE_CATALYST = "catalyst"
STAGE_SCORE = "score"
STAGE_BRIEFING = "briefing"
STAGE_DASHBOARD = "dashboard"
STAGE_HUMAN_REVIEW = "human_review"
STAGE_ADE = "ade"

# Required core composition order (Issue #126). Optional HR/ADE append to executed_stages.
STAGE_ORDER: tuple[str, ...] = (
    STAGE_WATCHLIST,
    STAGE_GAP,
    STAGE_CATALYST,
    STAGE_SCORE,
    STAGE_BRIEFING,
    STAGE_DASHBOARD,
)

MODEL_PARTICIPATION = "UNAUTHORIZED"
BROKER_EXECUTION = "DENIED / DEFERRED"
