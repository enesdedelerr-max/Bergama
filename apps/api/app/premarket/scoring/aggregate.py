"""Aggregation Engine for Premarket Scoring."""

from __future__ import annotations

from decimal import Decimal

from app.premarket.errors import ScoreDomainError, ScoreValidationError
from app.premarket.scoring.models import ScoreComponents
from app.premarket.scoring.normalize import quantize_unit_component
from app.premarket.scoring.policy import (
    FEATURE_CATALYST_PRESENCE,
    FEATURE_GAP_MAGNITUDE,
    FEATURE_WATCHLIST_RANK,
    SCORE_QUANTUM,
    SCORE_ROUNDING,
)
from app.premarket.scoring.ports import PolicyParams, QuantizedScore, WeightedTerms


def aggregate_terms(terms: WeightedTerms, *, params: PolicyParams) -> QuantizedScore:
    """Compute quantized Premarket Score via Policy Version linear weighted sum."""
    _ = params
    by_id = {term.feature_id: term for term in terms.terms}
    watchlist_term = by_id.get(FEATURE_WATCHLIST_RANK)
    if watchlist_term is None or not watchlist_term.present:
        raise ScoreValidationError(detail=f"missing_required_feature:{FEATURE_WATCHLIST_RANK}")
    if watchlist_term.watchlist_rank is None or watchlist_term.watchlist_rule_id is None:
        raise ScoreValidationError(detail="missing_watchlist_rank_metadata")

    gap_term = by_id.get(FEATURE_GAP_MAGNITUDE)
    catalyst_term = by_id.get(FEATURE_CATALYST_PRESENCE)

    raw = Decimal("0")
    source_identifiers: list[str] = []
    for term in terms.terms:
        raw += term.contribution
        source_identifiers.extend(term.source_identifiers)

    score = raw.quantize(SCORE_QUANTUM, rounding=SCORE_ROUNDING)
    if not score.is_finite() or score < Decimal("0") or score > Decimal("1"):
        raise ScoreDomainError(detail=f"score_out_of_domain:{score}")

    components = ScoreComponents(
        watchlist_rank=quantize_unit_component(
            watchlist_term.value, field_name=FEATURE_WATCHLIST_RANK
        ),
        gap_magnitude=(
            quantize_unit_component(gap_term.value, field_name=FEATURE_GAP_MAGNITUDE)
            if gap_term is not None and gap_term.present
            else None
        ),
        catalyst_presence=(
            quantize_unit_component(catalyst_term.value, field_name=FEATURE_CATALYST_PRESENCE)
            if catalyst_term is not None and catalyst_term.present
            else None
        ),
    )

    gap_record_id = gap_term.gap_record_id if gap_term is not None and gap_term.present else None
    catalyst_ids = (
        catalyst_term.source_identifiers
        if catalyst_term is not None and catalyst_term.present
        else ()
    )

    return QuantizedScore(
        instrument_key=terms.instrument_key,
        local_symbol=terms.local_symbol,
        score=score,
        components=components,
        watchlist_rank=watchlist_term.watchlist_rank,
        watchlist_rule_id=watchlist_term.watchlist_rule_id,
        gap_record_id=gap_record_id,
        catalyst_source_identifiers=catalyst_ids,
        source_identifiers=tuple(dict.fromkeys(source_identifiers)),
    )
