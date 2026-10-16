"""Premarket Analyst Projection Core Policy Version v1 constants."""

from __future__ import annotations

from typing import Final, Literal

ANALYST_DEFINITION_VERSION_V1: Final = "premarket-analyst.definition.v1"
POLICY_VERSION_V1: Final = "premarket-analyst.policy.v1"
IDENTITY_SPECIFICATION_V1: Final = "premarket-analyst.identity.v1"
PROVENANCE_SPECIFICATION_V1: Final = "premarket-analyst.provenance.v1"
DIGEST_METHOD_V1: Final = "canonical_payload_sha256_v1"
ORDERING_POLICY_V1: Final = "instrument_key_asc_then_stable_id_asc.v1"
REPLAY_EQUALITY_POLICY_V1: Final = "replay_equality.structural_complete.v1"
OUTPUT_COMPLETENESS_POLICY_V1: Final = "output_completeness.exactly_one_complete_artifact.v1"

CANONICAL_UTC_CONVENTION_ID: Final = "utc_aware_instant_v1"

EvaluationStateLiteral = Literal[
    "EVALUABLE",
    "INSUFFICIENT_EVIDENCE",
    "NOT_EVALUABLE",
    "ABSTAIN",
]

# Deterministic multi-condition collapse only. NOT risk severity. NOT equivalence.
EVALUATION_STATE_COLLAPSE_ORDER: Final[tuple[EvaluationStateLiteral, ...]] = (
    "NOT_EVALUABLE",
    "ABSTAIN",
    "INSUFFICIENT_EVIDENCE",
    "EVALUABLE",
)

RISK_FLAG_CATEGORIES: Final[frozenset[str]] = frozenset(
    {
        "MISSING_DATA",
        "STALE_DATA",
        "CONFLICTING_EVIDENCE",
        "WEAK_CATALYST_COVERAGE",
        "FRESHNESS_CONCERN",
        "STAGE_FAILURE_PRESENT",
        "UNSUPPORTED_EVALUATION",
        "NOT_EVALUABLE_INPUT",
    }
)

CompletenessClass = Literal["required", "optional"]

# Package-local required/optional matrix aligned to Policy §§11–13 concepts.
# Does not invent numeric staleness thresholds. Does not mutate frozen Policy.
FIELD_COMPLETENESS_MATRIX: Final[dict[str, CompletenessClass]] = {
    # §11 Structured Market Summary
    "market_summary.as_of": "required",
    "market_summary.watchlist_count": "required",
    "market_summary.watchlist_membership_refs": "required",
    "market_summary.gap_coverage_aggregates": "required",
    "market_summary.catalyst_coverage_aggregates": "required",
    "market_summary.score_dashboard_refs": "required",
    "market_summary.data_completeness_markers": "required",
    "market_summary.provenance": "required",
    # §12 Structured Catalyst Summary
    "catalyst_summary.as_of": "required",
    "catalyst_summary.records": "optional",
    "catalyst_summary.absence_marker": "optional",
    "catalyst_summary.provenance": "required",
    # §13 Narrow Structured Thesis
    "thesis.instrument_key": "required",
    "thesis.as_of": "required",
    "thesis.supporting_evidence_refs": "required",
    "thesis.counter_evidence_refs": "optional",
    "thesis.observed_conditions": "required",
    "thesis.informational_invalidation_conditions": "required",
    "thesis.uncertainty_markers": "required",
    "thesis.evaluation_state": "required",
    "thesis.provenance": "required",
}

PROHIBITED_THESIS_VOCABULARY: Final[frozenset[str]] = frozenset(
    {
        "BUY",
        "SELL",
        "HOLD",
        "entry",
        "exit",
        "entry price",
        "exit price",
        "stop-loss",
        "price target",
        "position size",
        "expected return",
        "trade signal",
        "trade instruction",
        "order intent",
        "broker intent",
        "broker instruction",
        "free-form thesis prose",
    }
)

PROHIBITED_INVALIDATION_VOCABULARY: Final[frozenset[str]] = frozenset(
    {
        "EXIT_TRADE",
        "CLOSE_POSITION",
        "RECOMMEND_CLOSE_POSITION",
        "SET_STOP_LOSS",
        "TRIGGER_STOP_LOSS",
        "CANCEL_ORDER",
        "CREATE_ORDER",
        "MODIFY_ORDER",
        "CHANGE_POSITION_SIZE",
        "MUTATE_PORTFOLIO_STATE",
        "INVOKE_BROKER_ACTION",
    }
)
