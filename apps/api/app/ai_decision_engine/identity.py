"""Canonical ADE decision identity for authoritative outcomes only."""

from __future__ import annotations

from app.ai_decision_engine.models import AdeConfig
from app.ai_decision_engine.policy import (
    ACCEPTANCE_SPECIFICATION_V1,
    DIGEST_METHOD_V1,
    IDENTITY_SPECIFICATION_V1,
    POLICY_VERSION_V1,
    PROVENANCE_SPECIFICATION_V1,
)
from app.human_review import HumanReviewOutput
from app.strategy.keys import strategy_sha256


def build_ade_decision_id(
    *,
    human_review: HumanReviewOutput,
    config: AdeConfig,
) -> str:
    """
    Return sha256 hex ADE-owned identity for an authoritative outcome.

    Explicit abstention is outside the canonical decision identity domain.
    """
    if config.digest_method_id != DIGEST_METHOD_V1:
        msg = f"unsupported_digest_method:{config.digest_method_id}"
        raise ValueError(msg)
    return strategy_sha256(_canonical_identity_payload(human_review=human_review, config=config))


def _canonical_identity_payload(
    *,
    human_review: HumanReviewOutput,
    config: AdeConfig,
) -> dict[str, object]:
    provenance = human_review.provenance
    return {
        "schema": IDENTITY_SPECIFICATION_V1,
        "policy_version_id": POLICY_VERSION_V1,
        "identity_specification_id": IDENTITY_SPECIFICATION_V1,
        "provenance_specification_id": PROVENANCE_SPECIFICATION_V1,
        "acceptance_specification_id": ACCEPTANCE_SPECIFICATION_V1,
        "digest_method_id": DIGEST_METHOD_V1,
        "as_of": human_review.as_of,
        "configuration": config.model_dump(mode="python"),
        "human_review_output_id": human_review.human_review_output_id,
        "human_review_policy_version_id": human_review.policy_version_id,
        "human_review_identity_specification_id": human_review.identity_specification_id,
        "human_review_provenance_specification_id": human_review.provenance_specification_id,
        "human_review_config_fingerprint": provenance.config_fingerprint,
        "human_review_input_fingerprint": provenance.input_fingerprint,
        "recorded_attestation_fingerprint": provenance.recorded_attestation_fingerprint,
        "recorded_attestation_payload": human_review.attestation.recorded_payload,
    }
