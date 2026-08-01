"""Normalization Engine for Premarket Scoring."""

from __future__ import annotations

from decimal import Decimal

from app.premarket.errors import ScoreDomainError, ScoreValidationError
from app.premarket.scoring.policy import SCORE_QUANTUM, SCORE_ROUNDING
from app.premarket.scoring.ports import (
    AbsentFeature,
    FeatureObservation,
    NormalizedComponent,
    PolicyParams,
)


def quantize_unit_component(value: Decimal, *, field_name: str) -> Decimal:
    """Quantize a unit-interval Decimal and reject out-of-domain values."""
    if not value.is_finite():
        raise ScoreDomainError(detail=f"non_finite_component:{field_name}")
    quantized = value.quantize(SCORE_QUANTUM, rounding=SCORE_ROUNDING)
    if quantized < Decimal("0") or quantized > Decimal("1"):
        raise ScoreDomainError(detail=f"component_out_of_domain:{field_name}:{quantized}")
    return quantized


def normalize_observation(
    observation: FeatureObservation | AbsentFeature,
    *,
    params: PolicyParams,
) -> NormalizedComponent | AbsentFeature:
    """Normalize one feature observation into a ``[0, 1]`` component.

    Feature Specs emit already-bounded raw values; this stage quantizes and
    validates domain. ``params`` is accepted for Policy Version extensibility.
    """
    _ = params
    if isinstance(observation, AbsentFeature):
        return observation
    if not isinstance(observation, FeatureObservation):
        raise ScoreValidationError(detail=f"unsupported_observation:{type(observation).__name__}")

    value = quantize_unit_component(observation.raw_value, field_name=observation.feature_id)
    return NormalizedComponent(
        feature_id=observation.feature_id,
        value=value,
        source_identifiers=observation.source_identifiers,
        gap_record_id=observation.gap_record_id,
        watchlist_rank=observation.watchlist_rank,
        watchlist_rule_id=observation.watchlist_rule_id,
    )


def normalize_observations(
    observations: tuple[FeatureObservation | AbsentFeature, ...],
    *,
    params: PolicyParams,
) -> tuple[NormalizedComponent | AbsentFeature, ...]:
    """Normalize all observations for one instrument."""
    return tuple(normalize_observation(item, params=params) for item in observations)
