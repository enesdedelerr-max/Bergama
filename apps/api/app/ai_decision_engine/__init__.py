"""AI Decision Engine Foundation public exports."""

from __future__ import annotations

from app.ai_decision_engine.engine import evaluate_ade, evaluate_ade_from_parts
from app.ai_decision_engine.errors import (
    AdeError,
    AdeModelParticipationError,
    AdeReplayInequalityError,
    AdeUnauthorizedInputError,
    AdeUnsupportedPolicyError,
    AdeValidationError,
)
from app.ai_decision_engine.models import (
    AdeConfig,
    AdeEvaluationRequest,
    AdeOutcomeKind,
    AdeProvenance,
    AdeResult,
)
from app.ai_decision_engine.policy import (
    ACCEPTANCE_SPECIFICATION_V1,
    CANONICAL_UTC_CONVENTION_ID,
    DERIVATION_ATTRIBUTION_V1,
    DIGEST_METHOD_V1,
    IDENTITY_SPECIFICATION_V1,
    MODEL_PARTICIPATION,
    POLICY_VERSION_V1,
    PROVENANCE_SPECIFICATION_V1,
    REPLAY_EQUALITY_POLICY_V1,
    REQUIRED_UPSTREAM_HUMAN_REVIEW_IDENTITY_SPECIFICATION_ID,
    REQUIRED_UPSTREAM_HUMAN_REVIEW_POLICY_VERSION_ID,
    REQUIRED_UPSTREAM_HUMAN_REVIEW_PROVENANCE_SPECIFICATION_ID,
)
from app.ai_decision_engine.reasons import FROZEN_REASON_FAMILIES, AdeReasonFamily
from app.ai_decision_engine.replay import assert_replay_equal, reevaluate

__all__ = [
    "ACCEPTANCE_SPECIFICATION_V1",
    "CANONICAL_UTC_CONVENTION_ID",
    "DERIVATION_ATTRIBUTION_V1",
    "DIGEST_METHOD_V1",
    "FROZEN_REASON_FAMILIES",
    "IDENTITY_SPECIFICATION_V1",
    "MODEL_PARTICIPATION",
    "POLICY_VERSION_V1",
    "PROVENANCE_SPECIFICATION_V1",
    "REPLAY_EQUALITY_POLICY_V1",
    "REQUIRED_UPSTREAM_HUMAN_REVIEW_IDENTITY_SPECIFICATION_ID",
    "REQUIRED_UPSTREAM_HUMAN_REVIEW_POLICY_VERSION_ID",
    "REQUIRED_UPSTREAM_HUMAN_REVIEW_PROVENANCE_SPECIFICATION_ID",
    "AdeConfig",
    "AdeError",
    "AdeEvaluationRequest",
    "AdeModelParticipationError",
    "AdeOutcomeKind",
    "AdeProvenance",
    "AdeReasonFamily",
    "AdeReplayInequalityError",
    "AdeResult",
    "AdeUnauthorizedInputError",
    "AdeUnsupportedPolicyError",
    "AdeValidationError",
    "assert_replay_equal",
    "evaluate_ade",
    "evaluate_ade_from_parts",
    "reevaluate",
]
