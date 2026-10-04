"""ADE provenance preserving Human Review references without ownership transfer."""

from __future__ import annotations

from datetime import datetime

from app.ai_decision_engine.models import AdeConfig, AdeProvenance
from app.ai_decision_engine.policy import (
    ACCEPTANCE_SPECIFICATION_V1,
    DERIVATION_ATTRIBUTION_V1,
    DIGEST_METHOD_V1,
    IDENTITY_SPECIFICATION_V1,
    POLICY_VERSION_V1,
    PROVENANCE_SPECIFICATION_V1,
)
from app.human_review import HumanReviewOutput
from app.strategy.keys import strategy_sha256


def _is_sha256_hex(value: object) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip().lower()
    return len(text) == 64 and all(ch in "0123456789abcdef" for ch in text)


def build_config_fingerprint(config: AdeConfig) -> str:
    """Deterministic fingerprint of ADE configuration and Policy binding."""
    return strategy_sha256(
        {
            "config": config.model_dump(mode="python"),
            "policy_version_id": POLICY_VERSION_V1,
            "identity_specification_id": IDENTITY_SPECIFICATION_V1,
            "provenance_specification_id": PROVENANCE_SPECIFICATION_V1,
            "acceptance_specification_id": ACCEPTANCE_SPECIFICATION_V1,
            "digest_method_id": DIGEST_METHOD_V1,
            "derivation_attribution_id": DERIVATION_ATTRIBUTION_V1,
        }
    )


def build_evidence_fingerprint(
    *,
    human_review: HumanReviewOutput | None,
    as_of: datetime,
) -> str:
    """Deterministic fingerprint of authorized evidence actually considered."""
    if human_review is None:
        return strategy_sha256({"as_of": as_of, "human_review": None})
    provenance = human_review.provenance
    return strategy_sha256(
        {
            "as_of": as_of,
            "human_review_output_id": human_review.human_review_output_id,
            "human_review_policy_version_id": human_review.policy_version_id,
            "human_review_identity_specification_id": human_review.identity_specification_id,
            "human_review_provenance_specification_id": human_review.provenance_specification_id,
            "human_review_config_fingerprint": provenance.config_fingerprint,
            "human_review_input_fingerprint": provenance.input_fingerprint,
            "recorded_attestation_fingerprint": provenance.recorded_attestation_fingerprint,
            "recorded_attestation_payload": human_review.attestation.recorded_payload,
            "human_review_as_of": human_review.as_of,
        }
    )


def build_ade_provenance(
    *,
    human_review: HumanReviewOutput | None,
    as_of: datetime,
    config: AdeConfig,
) -> AdeProvenance:
    """Build ADE provenance referencing HR public identity/provenance without ownership transfer."""
    config_fingerprint = build_config_fingerprint(config)
    if human_review is None:
        return AdeProvenance(
            policy_version_id=POLICY_VERSION_V1,
            identity_specification_id=IDENTITY_SPECIFICATION_V1,
            provenance_specification_id=PROVENANCE_SPECIFICATION_V1,
            acceptance_specification_id=ACCEPTANCE_SPECIFICATION_V1,
            digest_method_id=DIGEST_METHOD_V1,
            derivation_attribution_id=DERIVATION_ATTRIBUTION_V1,
            as_of=as_of,
            human_review_output_id=None,
            human_review_policy_version_id=None,
            human_review_identity_specification_id=None,
            human_review_provenance_specification_id=None,
            human_review_config_fingerprint=None,
            human_review_input_fingerprint=None,
            recorded_attestation_fingerprint=None,
            recorded_attestation_payload=None,
            config_fingerprint=config_fingerprint,
            evidence_fingerprint=build_evidence_fingerprint(human_review=None, as_of=as_of),
        )

    provenance = human_review.provenance
    return AdeProvenance(
        policy_version_id=POLICY_VERSION_V1,
        identity_specification_id=IDENTITY_SPECIFICATION_V1,
        provenance_specification_id=PROVENANCE_SPECIFICATION_V1,
        acceptance_specification_id=ACCEPTANCE_SPECIFICATION_V1,
        digest_method_id=DIGEST_METHOD_V1,
        derivation_attribution_id=DERIVATION_ATTRIBUTION_V1,
        as_of=as_of,
        human_review_output_id=(
            human_review.human_review_output_id
            if _is_sha256_hex(human_review.human_review_output_id)
            else None
        ),
        human_review_policy_version_id=human_review.policy_version_id or None,
        human_review_identity_specification_id=human_review.identity_specification_id or None,
        human_review_provenance_specification_id=(human_review.provenance_specification_id or None),
        human_review_config_fingerprint=(
            provenance.config_fingerprint if _is_sha256_hex(provenance.config_fingerprint) else None
        ),
        human_review_input_fingerprint=(
            provenance.input_fingerprint if _is_sha256_hex(provenance.input_fingerprint) else None
        ),
        recorded_attestation_fingerprint=(
            provenance.recorded_attestation_fingerprint
            if _is_sha256_hex(provenance.recorded_attestation_fingerprint)
            else None
        ),
        recorded_attestation_payload=human_review.attestation.recorded_payload,
        config_fingerprint=config_fingerprint,
        evidence_fingerprint=build_evidence_fingerprint(human_review=human_review, as_of=as_of),
    )
