"""Pipeline wiring helpers for Premarket Scoring stages."""

from __future__ import annotations

from app.premarket.scoring.aggregate import aggregate_terms
from app.premarket.scoring.features import extract_features
from app.premarket.scoring.identity import build_score_record_id
from app.premarket.scoring.models import ScoreCollection
from app.premarket.scoring.normalize import normalize_observations
from app.premarket.scoring.ordering import order_score_drafts
from app.premarket.scoring.output import to_score_collection
from app.premarket.scoring.ports import (
    BoundPolicyContext,
    ScoreIdentityInput,
    ScoreRecordDraft,
    ValidatedScoreRequest,
)
from app.premarket.scoring.provenance import build_collection_provenance
from app.premarket.scoring.validate_output import validate_score_collection
from app.premarket.scoring.weights import apply_weights


def run_scoring_pipeline(
    request: ValidatedScoreRequest,
    bound: BoundPolicyContext,
) -> ScoreCollection:
    """Execute the full scoring pipeline for a validated request."""
    observations_by_instrument = extract_features(request, bound)
    drafts: list[ScoreRecordDraft] = []

    entries_by_key = {entry.instrument_key: entry for entry in request.watchlist.entries}
    for instrument_key, observations in observations_by_instrument.items():
        entry = entries_by_key[instrument_key]
        normalized = normalize_observations(observations, params=bound.params)
        weighted = apply_weights(
            entry=entry,
            components=normalized,
            profile=bound.weight_profile,
        )
        quantized = aggregate_terms(weighted, params=bound.params)
        identity_input = ScoreIdentityInput(
            policy_version_id=bound.params.policy_version_id,
            weight_profile_id=bound.weight_profile.weight_profile_id,
            instrument_key=quantized.instrument_key,
            as_of=request.as_of,
            score=quantized.score,
            components=quantized.components,
            watchlist_rank=quantized.watchlist_rank,
            watchlist_rule_id=quantized.watchlist_rule_id,
            gap_record_id=quantized.gap_record_id,
            catalyst_source_identifiers=quantized.catalyst_source_identifiers,
        )
        score_record_id = build_score_record_id(bound.identity_builder, identity_input)
        drafts.append(
            ScoreRecordDraft(
                score_record_id=score_record_id,
                instrument_key=quantized.instrument_key,
                local_symbol=quantized.local_symbol,
                score=quantized.score,
                components=quantized.components,
                policy_version_id=bound.params.policy_version_id,
                weight_profile_id=bound.weight_profile.weight_profile_id,
                as_of=request.as_of,
                watchlist_rank=quantized.watchlist_rank,
                watchlist_rule_id=quantized.watchlist_rule_id,
                gap_record_id=quantized.gap_record_id,
                catalyst_source_identifiers=quantized.catalyst_source_identifiers,
                source_identifiers=quantized.source_identifiers,
            )
        )

    ordered = order_score_drafts(drafts, ordering_policy_id=bound.ordering_policy_id)
    provenance = build_collection_provenance(
        request=request,
        bound=bound,
        drafts=ordered,
    )
    collection = to_score_collection(
        as_of=request.as_of,
        drafts=ordered,
        provenance=provenance,
    )
    return validate_score_collection(collection, request=request, bound=bound)
