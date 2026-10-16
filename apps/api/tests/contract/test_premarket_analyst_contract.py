"""Contract tests for Premarket Analyst Projection Core artifact envelope."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.premarket.catalyst.models import CatalystCollection, CatalystProvenance, CatalystRecord
from app.premarket.gap.models import GapCollection, GapProvenance, GapRecord
from app.premarket.scoring.models import (
    ScoreCollection,
    ScoreComponents,
    ScoreProvenance,
    ScoreRecord,
)
from app.premarket.watchlist.models import Watchlist, WatchlistEntry, WatchlistProvenance
from app.premarket_analyst import project_analyst
from app.premarket_analyst.models import AnalystProjectionRequest, PremarketAnalystArtifact
from app.premarket_analyst.policy import (
    ANALYST_DEFINITION_VERSION_V1,
    EVALUATION_STATE_COLLAPSE_ORDER,
    RISK_FLAG_CATEGORIES,
)

AS_OF = datetime(2026, 7, 17, 14, 0, 0, tzinfo=UTC)
HEX = "b" * 64


def _request() -> AnalystProjectionRequest:
    key = "bergama:equity:us:aapl"
    watchlist = Watchlist(
        evaluation_timestamp=AS_OF,
        entries=(
            WatchlistEntry(
                instrument_key=key,
                local_symbol="AAPL",
                evaluation_timestamp=AS_OF,
                rank=1,
                inclusion_reason="core",
                rule_id="allowlist",
            ),
        ),
        provenance=WatchlistProvenance(
            config_fingerprint=HEX,
            input_fingerprint=HEX,
            ordering_policy_id="rule_priority_asc_instrument_key_asc",
            source_identifiers=(key,),
        ),
    )
    gaps = GapCollection(
        as_of=AS_OF,
        records=(
            GapRecord(
                gap_record_id="1" * 64,
                instrument_key=key,
                local_symbol="AAPL",
                previous_session_close=Decimal("100"),
                current_session_open=Decimal("101"),
                gap_percent=Decimal("1"),
                gap_direction="up",
                event_time=AS_OF - timedelta(hours=1),
                known_at=AS_OF - timedelta(minutes=30),
                as_of=AS_OF,
                selection_policy_id="two_bars_by_close_time_v1",
            ),
        ),
        provenance=GapProvenance(
            config_fingerprint=HEX,
            input_fingerprint=HEX,
            ordering_policy_id="abs_gap_desc_instrument_key_asc_id_asc",
            selection_policy_id="two_bars_by_close_time_v1",
        ),
    )
    catalysts = CatalystCollection(
        as_of=AS_OF,
        records=(
            CatalystRecord(
                catalyst_record_id="2" * 64,
                source_event_id="evt",
                source_content_fingerprint=HEX,
                instrument_key=key,
                local_symbol="AAPL",
                catalyst_type="earnings",
                event_time=AS_OF - timedelta(hours=2),
                known_at=AS_OF - timedelta(hours=1),
                as_of=AS_OF,
                source_provider="fixture",
                rule_id="rule",
            ),
        ),
        provenance=CatalystProvenance(
            config_fingerprint=HEX,
            input_fingerprint=HEX,
            ordering_policy_id="known_at_asc_event_time_asc_type_asc_instrument_key_asc_id_asc",
        ),
    )
    scores = ScoreCollection(
        as_of=AS_OF,
        records=(
            ScoreRecord(
                score_record_id="3" * 64,
                instrument_key=key,
                local_symbol="AAPL",
                score=Decimal("0.4"),
                components=ScoreComponents(watchlist_rank=Decimal("1")),
                policy_version_id="premarket.scoring.policy.v1",
                weight_profile_id="default_v1",
                as_of=AS_OF,
                watchlist_rank=1,
                watchlist_rule_id="allowlist",
            ),
        ),
        provenance=ScoreProvenance(
            config_fingerprint=HEX,
            input_fingerprint=HEX,
            ordering_policy_id="score_desc_instrument_key_asc_score_record_id_asc",
            policy_version_id="premarket.scoring.policy.v1",
            weight_profile_id="default_v1",
        ),
    )
    return AnalystProjectionRequest(
        as_of=AS_OF,
        watchlist=watchlist,
        gaps=gaps,
        catalysts=catalysts,
        scores=scores,
    )


def test_artifact_envelope_contract_fields() -> None:
    artifact = project_analyst(_request())
    assert isinstance(artifact, PremarketAnalystArtifact)
    assert set(PremarketAnalystArtifact.model_fields) >= {
        "analyst_artifact_id",
        "analyst_definition_version",
        "as_of",
        "evaluation_state",
        "market_summary",
        "catalyst_summary",
        "theses",
        "risk_flags",
        "provenance",
    }
    assert artifact.analyst_definition_version == ANALYST_DEFINITION_VERSION_V1
    assert artifact.evaluation_state in EVALUATION_STATE_COLLAPSE_ORDER
    assert artifact.as_of.tzinfo is not None
    assert len(artifact.analyst_artifact_id) == 64
    assert artifact.market_summary.watchlist_count >= 1
    assert artifact.provenance.input_fingerprint
    assert artifact.provenance.config_fingerprint


def test_risk_flag_categories_closed_set() -> None:
    artifact = project_analyst(_request())
    for flag in artifact.risk_flags:
        assert flag.category in RISK_FLAG_CATEGORIES


def test_identity_stable_across_equivalent_requests() -> None:
    first = project_analyst(_request())
    second = project_analyst(_request())
    assert first.analyst_artifact_id == second.analyst_artifact_id
    assert first.provenance.input_fingerprint == second.provenance.input_fingerprint
