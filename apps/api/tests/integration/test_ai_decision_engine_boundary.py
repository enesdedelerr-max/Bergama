"""Integration boundary tests for ADE ↔ Human Review public contracts."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from app.ai_decision_engine import (
    POLICY_VERSION_V1,
    AdeOutcomeKind,
    AdeReasonFamily,
    evaluate_ade_from_parts,
)
from app.dashboard.engine import assemble_dashboard_from_parts
from app.human_review import assemble_human_review_from_parts
from app.premarket.gap.engine import scan_gaps_from_parts
from app.premarket.morning_briefing import assemble_briefing_from_parts
from app.premarket.scoring.engine import scan_scores_from_parts
from app.premarket.scoring.models import ScoreConfig
from app.premarket.watchlist.engine import generate_watchlist
from app.premarket.watchlist.models import (
    WatchlistCandidate,
    WatchlistConfig,
    WatchlistGenerationRequest,
    WatchlistInclusionRule,
)
from tests.support.market_data_fixtures import instrument, make_bar, source

AS_OF = datetime(2026, 7, 17, 14, 0, tzinfo=UTC)
DAY1 = datetime(2026, 7, 15, 20, 0, tzinfo=UTC)
DAY2 = datetime(2026, 7, 16, 20, 0, tzinfo=UTC)
ATTESTATION = "recorded-human-authority-v1"
ADE_ROOT = Path(__file__).resolve().parents[2] / "app" / "ai_decision_engine"


def _bar(
    instrument_key: str,
    symbol: str,
    close_time: datetime,
    open_p: str,
    close_p: str,
    sid: str,
):
    known = close_time + timedelta(minutes=1)
    return make_bar(
        instrument=instrument(instrument_key=instrument_key, local_symbol=symbol),
        source=source(provider="fixture", source_event_id=sid),
        occurred_at=close_time,
        effective_at=close_time,
        known_at=known,
        ingested_at=known + timedelta(seconds=1),
        window_start=close_time - timedelta(hours=24),
        window_end=close_time,
        close_time=close_time,
        open=Decimal(open_p),
        high=Decimal(close_p) + Decimal("1"),
        low=Decimal(open_p) - Decimal("1"),
        close=Decimal(close_p),
        volume=Decimal("1000"),
    )


def _authorized_human_review():
    watchlist = generate_watchlist(
        WatchlistGenerationRequest(
            candidates=(
                WatchlistCandidate(instrument_key="bergama:equity:us:aapl", local_symbol="AAPL"),
                WatchlistCandidate(instrument_key="bergama:equity:us:msft", local_symbol="MSFT"),
            ),
            as_of=AS_OF,
            config=WatchlistConfig(
                rules=(
                    WatchlistInclusionRule(
                        rule_id="core",
                        rule_priority=1,
                        inclusion_reason="approved",
                        allowed_instrument_keys=(
                            "bergama:equity:us:aapl",
                            "bergama:equity:us:msft",
                        ),
                    ),
                )
            ),
        )
    )
    bars = (
        _bar("bergama:equity:us:aapl", "AAPL", DAY1, "100", "100", "a1"),
        _bar("bergama:equity:us:aapl", "AAPL", DAY2, "110", "111", "a2"),
        _bar("bergama:equity:us:msft", "MSFT", DAY1, "50", "50", "m1"),
        _bar("bergama:equity:us:msft", "MSFT", DAY2, "55", "56", "m2"),
    )
    gaps = scan_gaps_from_parts(watchlist=watchlist, bars=bars, as_of=AS_OF)
    scores = scan_scores_from_parts(
        watchlist=watchlist,
        as_of=AS_OF,
        config=ScoreConfig(),
        gaps=gaps,
    )
    briefing = assemble_briefing_from_parts(scores=scores, as_of=AS_OF)
    dashboard = assemble_dashboard_from_parts(briefing=briefing, as_of=AS_OF)
    return assemble_human_review_from_parts(
        dashboard=dashboard, as_of=AS_OF, attestation=ATTESTATION
    )


def test_ade_consumes_human_review_public_output_end_to_end() -> None:
    review = _authorized_human_review()
    first = evaluate_ade_from_parts(human_review=review, as_of=AS_OF)
    second = evaluate_ade_from_parts(human_review=review, as_of=AS_OF)

    assert first.outcome_kind is AdeOutcomeKind.AUTHORITATIVE_DECISION
    assert first.reason_family is AdeReasonFamily.ACCEPTED_GOVERNED_EVIDENCE
    assert first.policy_version_id == POLICY_VERSION_V1
    assert first.human_review_output_id == review.human_review_output_id
    assert first.provenance.human_review_output_id == review.human_review_output_id
    assert first.provenance.recorded_attestation_payload == ATTESTATION
    assert first.model_dump(mode="python") == second.model_dump(mode="python")
    # Nested lineage must not grant ADE ownership of upstream dashboard identity.
    assert first.provenance.human_review_output_id != review.dashboard_output_id


def test_ade_package_does_not_depend_on_forbidden_bounded_contexts() -> None:
    forbidden_tokens = (
        "app.dashboard",
        "app.premarket",
        "app.risk",
        "app.portfolio",
        "app.orders",
        "app.broker",
        "openai",
        "anthropic",
    )
    for path in ADE_ROOT.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in text, f"{path} contains forbidden dependency {token}"
