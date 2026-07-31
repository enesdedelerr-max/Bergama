"""Provenance Builder for Premarket Scoring."""

from __future__ import annotations

from app.premarket.scoring.models import ScoreProvenance
from app.premarket.scoring.policy import ORDERING_POLICY_SCORE_DESC_INSTRUMENT_KEY_ASC_ID_ASC
from app.premarket.scoring.ports import BoundPolicyContext, ScoreRecordDraft, ValidatedScoreRequest
from app.strategy.keys import strategy_sha256


def build_config_fingerprint(
    request: ValidatedScoreRequest,
    bound: BoundPolicyContext,
) -> str:
    """Deterministic fingerprint of configuration and Policy Version binding."""
    return strategy_sha256(
        {
            "config": request.config.model_dump(mode="python"),
            "policy_version_id": bound.params.policy_version_id,
            "weight_profile_id": bound.weight_profile.weight_profile_id,
            "weights": {
                feature_id: str(weight)
                for feature_id, weight in bound.weight_profile.weights.items()
            },
            "gap_ref": str(bound.params.gap_ref),
            "identity_specification_id": bound.params.identity_specification_id,
            "ordering_policy_id": bound.ordering_policy_id,
        }
    )


def build_input_fingerprint(request: ValidatedScoreRequest) -> str:
    """Deterministic fingerprint of authorized inputs actually consumed."""
    return strategy_sha256(
        {
            "as_of": request.as_of,
            "watchlist": request.watchlist.model_dump(mode="python"),
            "catalysts": (
                None if request.catalysts is None else request.catalysts.model_dump(mode="python")
            ),
            "gaps": None if request.gaps is None else request.gaps.model_dump(mode="python"),
            "ordering_policy_id": ORDERING_POLICY_SCORE_DESC_INSTRUMENT_KEY_ASC_ID_ASC,
        }
    )


def build_collection_provenance(
    *,
    request: ValidatedScoreRequest,
    bound: BoundPolicyContext,
    drafts: tuple[ScoreRecordDraft, ...],
) -> ScoreProvenance:
    """Build collection-level provenance for a scored evaluation."""
    source_identifiers: list[str] = []
    for draft in drafts:
        source_identifiers.append(draft.score_record_id)
        source_identifiers.extend(draft.source_identifiers)
    return ScoreProvenance(
        config_fingerprint=build_config_fingerprint(request, bound),
        input_fingerprint=build_input_fingerprint(request),
        ordering_policy_id=bound.ordering_policy_id,
        policy_version_id=bound.params.policy_version_id,
        weight_profile_id=bound.weight_profile.weight_profile_id,
        source_identifiers=tuple(dict.fromkeys(source_identifiers)),
    )
