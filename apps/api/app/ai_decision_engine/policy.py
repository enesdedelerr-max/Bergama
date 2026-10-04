"""AI Decision Engine Policy Version v1 constants."""

from __future__ import annotations

POLICY_VERSION_V1 = "ai-decision-engine.policy.v1"
IDENTITY_SPECIFICATION_V1 = "ai-decision-engine.identity.v1"
PROVENANCE_SPECIFICATION_V1 = "ai-decision-engine.provenance.v1"
DIGEST_METHOD_V1 = "canonical_payload_sha256_v1"
ACCEPTANCE_SPECIFICATION_V1 = "ai-decision-engine.governed_acceptance.v1"
REPLAY_EQUALITY_POLICY_V1 = "ai-decision-engine.replay_equality.structural.v1"
DERIVATION_ATTRIBUTION_V1 = "ai-decision-engine.derivation.governed_acceptance.v1"

CANONICAL_UTC_CONVENTION_ID = "utc_aware_instant_v1"

# Sole authorized upstream Policy Version identity (Human Review public surface).
REQUIRED_UPSTREAM_HUMAN_REVIEW_POLICY_VERSION_ID = "human-review.policy.v1"
REQUIRED_UPSTREAM_HUMAN_REVIEW_IDENTITY_SPECIFICATION_ID = "human-review.identity.v1"
REQUIRED_UPSTREAM_HUMAN_REVIEW_PROVENANCE_SPECIFICATION_ID = "human-review.provenance.v1"

MODEL_PARTICIPATION = "UNAUTHORIZED"
