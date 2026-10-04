"""Contract tests for AI Decision Engine Foundation public surface."""

from __future__ import annotations

import ast
from datetime import UTC, datetime
from pathlib import Path

import app.ai_decision_engine as ade
from app.ai_decision_engine import (
    MODEL_PARTICIPATION,
    POLICY_VERSION_V1,
    AdeConfig,
    AdeEvaluationRequest,
    AdeOutcomeKind,
    AdeProvenance,
    AdeReasonFamily,
    AdeResult,
)
from app.ai_decision_engine import (
    __all__ as ade_all,
)
from app.dashboard.engine import assemble_dashboard_from_parts
from app.human_review import HumanReviewOutput, assemble_human_review_from_parts
from app.premarket.morning_briefing import assemble_briefing_from_parts
from app.premarket.scoring.engine import scan_scores
from app.premarket.scoring.models import ScoreConfig, ScoreRequest
from app.premarket.watchlist.models import Watchlist, WatchlistEntry, WatchlistProvenance

AS_OF = datetime(2026, 7, 17, 14, 0, tzinfo=UTC)
ATTESTATION = "recorded-human-authority-v1"
PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "app" / "ai_decision_engine"

FORBIDDEN_IMPORT_PREFIXES = (
    "app.dashboard",
    "app.premarket",
    "app.market_data.connectors",
    "app.risk",
    "app.portfolio",
    "app.strategy.engine",
    "app.orders",
    "app.broker",
    "app.features",
    "openai",
    "anthropic",
    "langchain",
    "llama",
    "transformers",
)

FORBIDDEN_HR_PRIVATE = (
    "app.human_review.validate_input",
    "app.human_review.validate_output",
    "app.human_review.pipeline",
    "app.human_review.engine",
    "app.human_review.identity",
    "app.human_review.provenance",
    "app.human_review.history",
    "app.human_review.ordering",
    "app.human_review.output",
    "app.human_review.errors",
)


def _human_review() -> HumanReviewOutput:
    watchlist = Watchlist(
        evaluation_timestamp=AS_OF,
        entries=(
            WatchlistEntry(
                instrument_key="bergama:equity:us:aapl",
                local_symbol="AAPL",
                evaluation_timestamp=AS_OF,
                rank=1,
                inclusion_reason="core",
                rule_id="allowlist",
            ),
        ),
        provenance=WatchlistProvenance(
            config_fingerprint="a" * 64,
            input_fingerprint="b" * 64,
            ordering_policy_id="rule_priority_asc_instrument_key_asc",
            source_identifiers=("bergama:equity:us:aapl",),
        ),
    )
    scores = scan_scores(ScoreRequest(watchlist=watchlist, as_of=AS_OF, config=ScoreConfig()))
    briefing = assemble_briefing_from_parts(scores=scores, as_of=AS_OF)
    dashboard = assemble_dashboard_from_parts(briefing=briefing, as_of=AS_OF)
    return assemble_human_review_from_parts(
        dashboard=dashboard, as_of=AS_OF, attestation=ATTESTATION
    )


def test_public_exports_are_controlled() -> None:
    expected = {
        "ACCEPTANCE_SPECIFICATION_V1",
        "CANONICAL_UTC_CONVENTION_ID",
        "DERIVATION_ATTRIBUTION_V1",
        "DIGEST_METHOD_V1",
        "FROZEN_REASON_FAMILIES",
        "IDENTITY_SPECIFICATION_V1",
        "MODEL_PARTICIPATION",
        "POLICY_VERSION_V1",
        "PROVENANCE_SPECIFICATION_V1",
        "REPLAY_EQUALITY_POLICY_V1",
        "REQUIRED_UPSTREAM_HUMAN_REVIEW_IDENTITY_SPECIFICATION_ID",
        "REQUIRED_UPSTREAM_HUMAN_REVIEW_POLICY_VERSION_ID",
        "REQUIRED_UPSTREAM_HUMAN_REVIEW_PROVENANCE_SPECIFICATION_ID",
        "AdeConfig",
        "AdeError",
        "AdeEvaluationRequest",
        "AdeModelParticipationError",
        "AdeOutcomeKind",
        "AdeProvenance",
        "AdeReasonFamily",
        "AdeReplayInequalityError",
        "AdeResult",
        "AdeUnauthorizedInputError",
        "AdeUnsupportedPolicyError",
        "AdeValidationError",
        "assert_replay_equal",
        "evaluate_ade",
        "evaluate_ade_from_parts",
        "reevaluate",
    }
    assert set(ade_all) == expected
    for name in ade_all:
        assert hasattr(ade, name)


def test_models_are_frozen_and_forbid_extra() -> None:
    for model in (AdeConfig, AdeEvaluationRequest, AdeProvenance, AdeResult):
        assert model.model_config.get("frozen") is True
        assert model.model_config.get("extra") == "forbid"


def test_outcome_kinds_are_exactly_frozen_pair() -> None:
    assert {member.value for member in AdeOutcomeKind} == {
        "authoritative_decision",
        "explicit_abstention",
    }


def test_package_imports_only_human_review_public_surface() -> None:
    for path in PACKAGE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module]
            else:
                continue
            for module in modules:
                for prefix in FORBIDDEN_IMPORT_PREFIXES:
                    assert not module.startswith(prefix), f"{path} imports {module}"
                for private in FORBIDDEN_HR_PRIVATE:
                    assert module != private, f"{path} imports private HR module {module}"
                if module.startswith("app.human_review"):
                    assert module == "app.human_review", (
                        f"{path} must import Human Review only via public package surface"
                    )


def test_no_model_or_trading_tokens_in_public_surface() -> None:
    public_names = " ".join(ade_all).lower()
    for token in (
        "llm",
        "prompt",
        "embedding",
        "openai",
        "broker",
        "order_intent",
        "oms",
        "buy",
        "sell",
        "no_trade",
    ):
        assert token not in public_names
    assert MODEL_PARTICIPATION == "UNAUTHORIZED"
    assert POLICY_VERSION_V1 == "ai-decision-engine.policy.v1"


def test_reason_family_contract_matches_policy() -> None:
    assert set(AdeReasonFamily) == {
        AdeReasonFamily.ACCEPTED_GOVERNED_EVIDENCE,
        AdeReasonFamily.MISSING_AUTHORIZED_EVIDENCE,
        AdeReasonFamily.INVALID_AUTHORIZED_EVIDENCE,
        AdeReasonFamily.STALE_EVIDENCE,
        AdeReasonFamily.CONFLICTING_OR_AMBIGUOUS_EVIDENCE,
        AdeReasonFamily.TEMPORAL_PIT_MISMATCH,
        AdeReasonFamily.IDENTITY_INSUFFICIENCY,
        AdeReasonFamily.PROVENANCE_INSUFFICIENCY,
        AdeReasonFamily.DETERMINISTIC_ACCEPTANCE_NOT_ESTABLISHED,
        AdeReasonFamily.POLICY_CONTEXT_INSUFFICIENCY,
    }


def test_evaluation_request_accepts_human_review_public_output_only() -> None:
    review = _human_review()
    request = AdeEvaluationRequest(human_review=review, as_of=AS_OF)
    assert isinstance(request.human_review, HumanReviewOutput)
