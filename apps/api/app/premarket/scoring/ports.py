"""Ports, protocols, and immutable pipeline value objects for Premarket Scoring."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Protocol

from app.premarket.catalyst.models import CatalystCollection
from app.premarket.gap.models import GapCollection
from app.premarket.scoring.models import (
    ScoreComponents,
    ScoreConfig,
)
from app.premarket.watchlist.models import Watchlist, WatchlistEntry


@dataclass(frozen=True, slots=True)
class PolicyParams:
    """Immutable Policy Version parameters consumed by pipeline stages."""

    policy_version_id: str
    weight_profile_id: str
    ordering_policy_id: str
    score_quantize_policy_id: str
    identity_specification_id: str
    gap_ref: Decimal


@dataclass(frozen=True, slots=True)
class WeightProfile:
    """Immutable weight profile owned by a Policy Version."""

    weight_profile_id: str
    weights: Mapping[str, Decimal]

    def __post_init__(self) -> None:
        object.__setattr__(self, "weights", MappingProxyType(dict(self.weights)))


@dataclass(frozen=True, slots=True)
class ValidatedScoreRequest:
    """Request admitted by the Input Validation Layer."""

    watchlist: Watchlist
    as_of: datetime
    config: ScoreConfig
    catalysts: CatalystCollection | None
    gaps: GapCollection | None


@dataclass(frozen=True, slots=True)
class InstrumentScoreContext:
    """Per-instrument extraction context under a single PIT evaluation."""

    entry: WatchlistEntry
    watchlist: Watchlist
    as_of: datetime
    catalysts: CatalystCollection | None
    gaps: GapCollection | None
    params: PolicyParams


@dataclass(frozen=True, slots=True)
class FeatureObservation:
    """Raw feature observation prior to normalization."""

    feature_id: str
    raw_value: Decimal
    source_identifiers: tuple[str, ...] = ()
    gap_record_id: str | None = None
    watchlist_rank: int | None = None
    watchlist_rule_id: str | None = None


@dataclass(frozen=True, slots=True)
class AbsentFeature:
    """Explicit absence of an authorized optional feature."""

    feature_id: str


@dataclass(frozen=True, slots=True)
class NormalizedComponent:
    """Normalized feature component in ``[0, 1]``."""

    feature_id: str
    value: Decimal
    source_identifiers: tuple[str, ...] = ()
    gap_record_id: str | None = None
    watchlist_rank: int | None = None
    watchlist_rule_id: str | None = None


@dataclass(frozen=True, slots=True)
class WeightedTerm:
    """Normalized component with attached Policy Version weight."""

    feature_id: str
    value: Decimal
    weight: Decimal
    contribution: Decimal
    present: bool
    source_identifiers: tuple[str, ...] = ()
    gap_record_id: str | None = None
    watchlist_rank: int | None = None
    watchlist_rule_id: str | None = None


@dataclass(frozen=True, slots=True)
class WeightedTerms:
    """Weighted term set for one instrument."""

    instrument_key: str
    local_symbol: str | None
    terms: tuple[WeightedTerm, ...]


@dataclass(frozen=True, slots=True)
class QuantizedScore:
    """Aggregated and quantized Premarket Score draft fragment."""

    instrument_key: str
    local_symbol: str | None
    score: Decimal
    components: ScoreComponents
    watchlist_rank: int
    watchlist_rule_id: str
    gap_record_id: str | None
    catalyst_source_identifiers: tuple[str, ...]
    source_identifiers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ScoreRecordDraft:
    """Internal immutable draft prior to public contract materialization."""

    score_record_id: str
    instrument_key: str
    local_symbol: str | None
    score: Decimal
    components: ScoreComponents
    policy_version_id: str
    weight_profile_id: str
    as_of: datetime
    watchlist_rank: int
    watchlist_rule_id: str
    gap_record_id: str | None
    catalyst_source_identifiers: tuple[str, ...]
    source_identifiers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ScoreIdentityInput:
    """Canonical inputs for deterministic score identity."""

    policy_version_id: str
    weight_profile_id: str
    instrument_key: str
    as_of: datetime
    score: Decimal
    components: ScoreComponents
    watchlist_rank: int
    watchlist_rule_id: str
    gap_record_id: str | None
    catalyst_source_identifiers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BoundPolicyContext:
    """Resolved Policy Version binder context for one evaluation."""

    params: PolicyParams
    weight_profile: WeightProfile
    feature_extractors: tuple[FeatureExtractor, ...]
    identity_builder: IdentityBuilder
    ordering_policy_id: str


class FeatureExtractor(Protocol):
    """Extracts one Policy Version feature observation for an instrument."""

    @property
    def feature_id(self) -> str: ...

    def extract(self, ctx: InstrumentScoreContext) -> FeatureObservation | AbsentFeature: ...


class IdentityBuilder(Protocol):
    """Builds deterministic score record identities."""

    def build_id(self, draft: ScoreIdentityInput) -> str: ...


class PolicyVersionBinder(Protocol):
    """Binds one Policy Version implementation into the scoring pipeline."""

    @property
    def policy_version_id(self) -> str: ...

    @property
    def weight_profile_id(self) -> str: ...

    def resolve_params(self) -> PolicyParams: ...

    def weight_profile(self) -> WeightProfile: ...

    def feature_extractors(self) -> Sequence[FeatureExtractor]: ...

    def identity_builder(self) -> IdentityBuilder: ...
