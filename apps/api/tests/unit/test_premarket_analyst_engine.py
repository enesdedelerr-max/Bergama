"""Unit tests for Premarket Analyst Projection Core (WS1)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from app.premarket.catalyst.models import CatalystCollection, CatalystProvenance, CatalystRecord
from app.premarket.gap.models import GapCollection, GapProvenance, GapRecord
from app.premarket.scoring.models import (
    ScoreCollection,
    ScoreComponents,
    ScoreProvenance,
    ScoreRecord,
)
from app.premarket.watchlist.models import Watchlist, WatchlistEntry, WatchlistProvenance
from app.premarket_analyst.engine import collapse_evaluation_states, project_analyst
from app.premarket_analyst.errors import (
    PremarketAnalystFailClosedError,
    PremarketAnalystPitConflictError,
    PremarketAnalystReplayInequalityError,
    PremarketAnalystUnsupportedPolicyError,
)
from app.premarket_analyst.models import AnalystConfig, AnalystProjectionRequest
from app.premarket_analyst.policy import (
    ANALYST_DEFINITION_VERSION_V1,
    EVALUATION_STATE_COLLAPSE_ORDER,
    FIELD_COMPLETENESS_MATRIX,
    RISK_FLAG_CATEGORIES,
)
from app.premarket_analyst.replay import assert_replay_equal, reproject

AS_OF = datetime(2026, 7, 17, 14, 0, 0, tzinfo=UTC)
HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64
HEX_D = "d" * 64
HEX_E = "e" * 64
HEX_F = "f" * 64


def _watchlist(*keys: str) -> Watchlist:
    entries = tuple(
        WatchlistEntry(
            instrument_key=key,
            local_symbol=key.split(":")[-1].upper(),
            evaluation_timestamp=AS_OF,
            rank=index + 1,
            inclusion_reason="core",
            rule_id="allowlist",
        )
        for index, key in enumerate(keys)
    )
    return Watchlist(
        evaluation_timestamp=AS_OF,
        entries=entries,
        provenance=WatchlistProvenance(
            config_fingerprint=HEX_A,
            input_fingerprint=HEX_B,
            ordering_policy_id="rule_priority_asc_instrument_key_asc",
            source_identifiers=tuple(keys),
        ),
    )


def _gaps(*keys: str) -> GapCollection:
    records = tuple(
        GapRecord(
            gap_record_id=(f"{index:064x}"),
            instrument_key=key,
            local_symbol=key.split(":")[-1].upper(),
            previous_session_close=Decimal("100"),
            current_session_open=Decimal("105"),
            gap_percent=Decimal("5"),
            gap_direction="up",
            event_time=AS_OF - timedelta(hours=1),
            known_at=AS_OF - timedelta(minutes=30),
            as_of=AS_OF,
            selection_policy_id="two_bars_by_close_time_v1",
        )
        for index, key in enumerate(keys, start=1)
    )
    return GapCollection(
        as_of=AS_OF,
        records=records,
        provenance=GapProvenance(
            config_fingerprint=HEX_C,
            input_fingerprint=HEX_D,
            ordering_policy_id="abs_gap_desc_instrument_key_asc_id_asc",
            selection_policy_id="two_bars_by_close_time_v1",
            source_identifiers=tuple(keys),
        ),
    )


def _catalysts(*keys: str) -> CatalystCollection:
    records = tuple(
        CatalystRecord(
            catalyst_record_id=(f"{index + 10:064x}"),
            source_event_id=f"evt-{index}",
            source_content_fingerprint=HEX_E,
            instrument_key=key,
            local_symbol=key.split(":")[-1].upper(),
            catalyst_type="earnings",
            event_time=AS_OF - timedelta(hours=2),
            known_at=AS_OF - timedelta(hours=1),
            as_of=AS_OF,
            source_provider="fixture",
            rule_id="rule-earnings",
        )
        for index, key in enumerate(keys, start=1)
    )
    return CatalystCollection(
        as_of=AS_OF,
        records=records,
        provenance=CatalystProvenance(
            config_fingerprint=HEX_E,
            input_fingerprint=HEX_F,
            ordering_policy_id="known_at_asc_event_time_asc_type_asc_instrument_key_asc_id_asc",
            source_identifiers=tuple(keys),
        ),
    )


def _scores(*keys: str) -> ScoreCollection:
    records = tuple(
        ScoreRecord(
            score_record_id=(f"{index + 20:064x}"),
            instrument_key=key,
            local_symbol=key.split(":")[-1].upper(),
            score=Decimal("0.5"),
            components=ScoreComponents(
                watchlist_rank=Decimal("1"),
                gap_magnitude=Decimal("0.5"),
                catalyst_presence=Decimal("0.5"),
            ),
            policy_version_id="premarket.scoring.policy.v1",
            weight_profile_id="default_v1",
            as_of=AS_OF,
            watchlist_rank=index,
            watchlist_rule_id="allowlist",
            gap_record_id=None,
            catalyst_source_identifiers=(),
        )
        for index, key in enumerate(keys, start=1)
    )
    return ScoreCollection(
        as_of=AS_OF,
        records=records,
        provenance=ScoreProvenance(
            config_fingerprint=HEX_A,
            input_fingerprint=HEX_C,
            ordering_policy_id="score_desc_instrument_key_asc_score_record_id_asc",
            policy_version_id="premarket.scoring.policy.v1",
            weight_profile_id="default_v1",
            source_identifiers=tuple(keys),
        ),
    )


def _full_request(*keys: str) -> AnalystProjectionRequest:
    return AnalystProjectionRequest(
        as_of=AS_OF,
        watchlist=_watchlist(*keys),
        gaps=_gaps(*keys),
        catalysts=_catalysts(*keys),
        scores=_scores(*keys),
        membership_complete=True,
    )


def test_happy_path_five_capabilities() -> None:
    artifact = project_analyst(_full_request("bergama:equity:us:aapl", "bergama:equity:us:msft"))
    assert artifact.analyst_definition_version == ANALYST_DEFINITION_VERSION_V1
    assert artifact.evaluation_state == "EVALUABLE"
    assert artifact.market_summary.watchlist_count == 2
    assert len(artifact.catalyst_summary.records) == 2
    assert len(artifact.theses) == 2
    assert artifact.catalyst_summary.absence_marker is False
    assert all(flag.category in RISK_FLAG_CATEGORIES for flag in artifact.risk_flags)


def test_replay_determinism() -> None:
    request = _full_request("bergama:equity:us:aapl")
    first = project_analyst(request)
    second = reproject(request)
    assert_replay_equal(first, second)
    third = project_analyst(request)
    assert first.model_dump(mode="python") == third.model_dump(mode="python")


def test_replay_inequality_detection() -> None:
    first = project_analyst(_full_request("bergama:equity:us:aapl"))
    second = project_analyst(_full_request("bergama:equity:us:msft"))
    with pytest.raises(PremarketAnalystReplayInequalityError):
        assert_replay_equal(first, second)


def test_collapse_order_not_equivalence() -> None:
    assert collapse_evaluation_states(("EVALUABLE", "NOT_EVALUABLE")) == "NOT_EVALUABLE"
    assert collapse_evaluation_states(("INSUFFICIENT_EVIDENCE", "ABSTAIN")) == "ABSTAIN"
    assert EVALUATION_STATE_COLLAPSE_ORDER[0] == "NOT_EVALUABLE"
    assert "ABSTAIN" != "NOT_EVALUABLE"
    assert "ABSTAIN" != "INSUFFICIENT_EVIDENCE"
    assert "NOT_EVALUABLE" != "INSUFFICIENT_EVIDENCE"


def test_partial_watchlist_insufficient_evidence() -> None:
    request = AnalystProjectionRequest(
        as_of=AS_OF,
        watchlist=_watchlist("bergama:equity:us:aapl"),
        gaps=_gaps("bergama:equity:us:aapl"),
        catalysts=_catalysts("bergama:equity:us:aapl"),
        scores=_scores("bergama:equity:us:aapl"),
        membership_complete=False,
    )
    artifact = project_analyst(request)
    assert artifact.evaluation_state == "INSUFFICIENT_EVIDENCE"
    assert artifact.market_summary.completeness.membership_complete is False


def test_conflicting_evidence_never_abstain() -> None:
    request = AnalystProjectionRequest(
        as_of=AS_OF,
        watchlist=_watchlist("bergama:equity:us:aapl"),
        gaps=_gaps("bergama:equity:us:aapl"),
        catalysts=_catalysts("bergama:equity:us:aapl"),
        scores=_scores("bergama:equity:us:msft"),
        membership_complete=True,
    )
    artifact = project_analyst(request)
    assert artifact.evaluation_state == "INSUFFICIENT_EVIDENCE"
    assert artifact.evaluation_state != "ABSTAIN"
    assert any(flag.category == "CONFLICTING_EVIDENCE" for flag in artifact.risk_flags)


def test_missing_gaps_not_evaluable() -> None:
    request = AnalystProjectionRequest(
        as_of=AS_OF,
        watchlist=_watchlist("bergama:equity:us:aapl"),
        gaps=None,
        catalysts=_catalysts("bergama:equity:us:aapl"),
        scores=_scores("bergama:equity:us:aapl"),
    )
    artifact = project_analyst(request)
    assert artifact.evaluation_state == "NOT_EVALUABLE"


def test_missing_scores_and_dashboard_not_evaluable() -> None:
    request = AnalystProjectionRequest(
        as_of=AS_OF,
        watchlist=_watchlist("bergama:equity:us:aapl"),
        gaps=_gaps("bergama:equity:us:aapl"),
        catalysts=_catalysts("bergama:equity:us:aapl"),
        scores=None,
        dashboard=None,
    )
    artifact = project_analyst(request)
    assert artifact.evaluation_state == "NOT_EVALUABLE"


def test_stale_catalyst_mapping() -> None:
    stale = CatalystRecord(
        catalyst_record_id="1" * 64,
        source_event_id="evt-stale",
        source_content_fingerprint=HEX_E,
        instrument_key="bergama:equity:us:aapl",
        local_symbol="AAPL",
        catalyst_type="earnings",
        event_time=AS_OF - timedelta(hours=2),
        known_at=AS_OF + timedelta(minutes=1),
        as_of=AS_OF,
        source_provider="fixture",
        rule_id="rule-earnings",
    )
    catalysts = CatalystCollection(
        as_of=AS_OF,
        records=(stale,),
        provenance=CatalystProvenance(
            config_fingerprint=HEX_E,
            input_fingerprint=HEX_F,
            ordering_policy_id="known_at_asc_event_time_asc_type_asc_instrument_key_asc_id_asc",
            source_identifiers=("bergama:equity:us:aapl",),
        ),
    )
    request = AnalystProjectionRequest(
        as_of=AS_OF,
        watchlist=_watchlist("bergama:equity:us:aapl"),
        gaps=_gaps("bergama:equity:us:aapl"),
        catalysts=catalysts,
        scores=_scores("bergama:equity:us:aapl"),
    )
    artifact = project_analyst(request)
    assert artifact.evaluation_state == "NOT_EVALUABLE"
    assert any(flag.category == "STALE_DATA" for flag in artifact.risk_flags)
    assert artifact.catalyst_summary.records == ()


def test_upstream_stage_failure_propagates() -> None:
    request = AnalystProjectionRequest(
        as_of=AS_OF,
        watchlist=_watchlist("bergama:equity:us:aapl"),
        gaps=_gaps("bergama:equity:us:aapl"),
        catalysts=_catalysts("bergama:equity:us:aapl"),
        scores=_scores("bergama:equity:us:aapl"),
        upstream_pipeline_failure_identity="stage:scoring:failed",
    )
    artifact = project_analyst(request)
    assert artifact.evaluation_state == "NOT_EVALUABLE"
    assert artifact.provenance.upstream_pipeline_failure_identity == "stage:scoring:failed"
    assert any(flag.category == "STAGE_FAILURE_PRESENT" for flag in artifact.risk_flags)


def test_pit_rejects_future_event_time() -> None:
    gaps = _gaps("bergama:equity:us:aapl")
    future = gaps.records[0].model_copy(update={"event_time": AS_OF + timedelta(minutes=5)})
    bad = GapCollection(as_of=AS_OF, records=(future,), provenance=gaps.provenance)
    request = AnalystProjectionRequest(
        as_of=AS_OF,
        watchlist=_watchlist("bergama:equity:us:aapl"),
        gaps=bad,
        catalysts=_catalysts("bergama:equity:us:aapl"),
        scores=_scores("bergama:equity:us:aapl"),
    )
    with pytest.raises(PremarketAnalystPitConflictError):
        project_analyst(request)


def test_malformed_request_fail_closed() -> None:
    with pytest.raises(PremarketAnalystFailClosedError):
        project_analyst({"as_of": "not-a-datetime"})


def test_unsupported_policy_fail_closed() -> None:
    with pytest.raises((PremarketAnalystUnsupportedPolicyError, Exception)):
        AnalystConfig(policy_version_id="other.policy")


def test_field_completeness_matrix_pins_policy_sections() -> None:
    assert FIELD_COMPLETENESS_MATRIX["market_summary.gap_coverage_aggregates"] == "required"
    assert FIELD_COMPLETENESS_MATRIX["catalyst_summary.records"] == "optional"
    assert FIELD_COMPLETENESS_MATRIX["thesis.instrument_key"] == "required"


def test_thesis_informational_only() -> None:
    artifact = project_analyst(_full_request("bergama:equity:us:aapl"))
    thesis = artifact.theses[0]
    assert "evidence_conditions_no_longer_satisfied" in thesis.informational_invalidation_conditions
    joined = " ".join(
        thesis.supporting_evidence_refs
        + thesis.observed_conditions
        + thesis.informational_invalidation_conditions
    )
    for banned in ("BUY", "SELL", "EXIT_TRADE", "CREATE_ORDER"):
        assert banned not in joined


def test_no_risk_severity_field() -> None:
    artifact = project_analyst(_full_request("bergama:equity:us:aapl"))
    for flag in artifact.risk_flags:
        assert not hasattr(flag, "severity")
        dumped = flag.model_dump()
        assert "severity" not in dumped


def test_package_isolation_from_unauthorized_modules() -> None:
    root = Path(__file__).resolve().parents[2] / "app" / "premarket_analyst"
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    assert "from fastapi" not in text
    assert "import fastapi" not in text
    assert "from app.broker" not in text
    assert "from app.routers" not in text
    assert "import alembic" not in text
    assert "openai" not in text.lower()
