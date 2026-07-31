"""Post-condition Validation Layer for Premarket Scoring."""

from __future__ import annotations

from decimal import Decimal

from app.premarket.errors import ScoreDomainError, ScoreInvariantError
from app.premarket.scoring.canonical import canonical_source_identifiers
from app.premarket.scoring.models import ScoreCollection, ScoreComponents
from app.premarket.scoring.ordering import score_sort_key
from app.premarket.scoring.policy import POLICY_VERSION_V1, WEIGHT_PROFILE_DEFAULT_V1
from app.premarket.scoring.ports import BoundPolicyContext, ScoreRecordDraft, ValidatedScoreRequest


def validate_score_collection(
    collection: ScoreCollection,
    *,
    request: ValidatedScoreRequest,
    bound: BoundPolicyContext,
) -> ScoreCollection:
    """Enforce Policy Version v1 post-conditions before return."""
    if collection.as_of != request.as_of:
        raise ScoreInvariantError(detail="as_of_mismatch")
    if collection.provenance.policy_version_id != POLICY_VERSION_V1:
        raise ScoreInvariantError(detail="policy_version_mismatch")
    if collection.provenance.weight_profile_id != WEIGHT_PROFILE_DEFAULT_V1:
        raise ScoreInvariantError(detail="weight_profile_mismatch")
    if collection.provenance.ordering_policy_id != bound.ordering_policy_id:
        raise ScoreInvariantError(detail="ordering_policy_mismatch")

    expected_order = tuple(
        sorted(
            (
                ScoreRecordDraft(
                    score_record_id=record.score_record_id,
                    instrument_key=record.instrument_key,
                    local_symbol=record.local_symbol,
                    score=record.score,
                    components=record.components,
                    policy_version_id=record.policy_version_id,
                    weight_profile_id=record.weight_profile_id,
                    as_of=record.as_of,
                    watchlist_rank=record.watchlist_rank,
                    watchlist_rule_id=record.watchlist_rule_id,
                    gap_record_id=record.gap_record_id,
                    catalyst_source_identifiers=record.catalyst_source_identifiers,
                    source_identifiers=(),
                )
                for record in collection.records
            ),
            key=score_sort_key,
        )
    )
    actual_ids = tuple(record.score_record_id for record in collection.records)
    expected_ids = tuple(draft.score_record_id for draft in expected_order)
    if actual_ids != expected_ids:
        raise ScoreInvariantError(detail="ordering_invariant_violated")

    for record in collection.records:
        if not record.score.is_finite():
            raise ScoreDomainError(detail=f"non_finite_score:{record.instrument_key}")
        if record.score < Decimal("0") or record.score > Decimal("1"):
            raise ScoreDomainError(detail=f"score_out_of_domain:{record.instrument_key}")
        _assert_components_in_domain(record.components, instrument_key=record.instrument_key)
        if record.catalyst_source_identifiers != canonical_source_identifiers(
            record.catalyst_source_identifiers
        ):
            raise ScoreInvariantError(detail=f"non_canonical_catalyst_ids:{record.instrument_key}")
        if record.policy_version_id != POLICY_VERSION_V1:
            raise ScoreInvariantError(detail=f"record_policy_mismatch:{record.instrument_key}")
        if record.weight_profile_id != WEIGHT_PROFILE_DEFAULT_V1:
            raise ScoreInvariantError(detail=f"record_weight_mismatch:{record.instrument_key}")
        if len(record.score_record_id) != 64:
            raise ScoreInvariantError(detail=f"invalid_score_record_id:{record.instrument_key}")

    return collection


def _assert_components_in_domain(components: ScoreComponents, *, instrument_key: str) -> None:
    """Reject any emitted component outside finite ``[0, 1]`` (no repair)."""
    checks: tuple[tuple[str, Decimal | None], ...] = (
        ("watchlist_rank", components.watchlist_rank),
        ("gap_magnitude", components.gap_magnitude),
        ("catalyst_presence", components.catalyst_presence),
    )
    for field_name, value in checks:
        if value is None:
            if field_name == "watchlist_rank":
                raise ScoreDomainError(
                    detail=f"missing_required_component:{instrument_key}:{field_name}"
                )
            continue
        if not value.is_finite() or value < Decimal("0") or value > Decimal("1"):
            raise ScoreDomainError(
                detail=f"component_out_of_domain:{instrument_key}:{field_name}:{value}"
            )
