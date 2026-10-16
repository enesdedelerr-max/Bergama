"""OIA-04 failure mapping matrix tests for Premarket Analyst WS1."""

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
from app.premarket_analyst.engine import project_analyst
from app.premarket_analyst.models import AnalystProjectionRequest

AS_OF = datetime(2026, 7, 17, 14, 0, 0, tzinfo=UTC)
HEX = "a" * 64


def _wl(*keys: str) -> Watchlist:
    entries = tuple(
        WatchlistEntry(
            instrument_key=key,
            local_symbol="X",
            evaluation_timestamp=AS_OF,
            rank=i + 1,
            inclusion_reason="core",
            rule_id="r",
        )
        for i, key in enumerate(keys)
    )
    return Watchlist(
        evaluation_timestamp=AS_OF,
        entries=entries,
        provenance=WatchlistProvenance(
            config_fingerprint=HEX,
            input_fingerprint=HEX,
            ordering_policy_id="rule_priority_asc_instrument_key_asc",
            source_identifiers=keys,
        ),
    )


def _gap(key: str, *, known_at: datetime | None = None) -> GapCollection:
    record = GapRecord(
        gap_record_id="1" * 64,
        instrument_key=key,
        local_symbol="X",
        previous_session_close=Decimal("1"),
        current_session_open=Decimal("1.1"),
        gap_percent=Decimal("0.1"),
        gap_direction="up",
        event_time=AS_OF - timedelta(hours=1),
        known_at=known_at or (AS_OF - timedelta(minutes=1)),
        as_of=AS_OF,
        selection_policy_id="two_bars_by_close_time_v1",
    )
    return GapCollection(
        as_of=AS_OF,
        records=(record,),
        provenance=GapProvenance(
            config_fingerprint=HEX,
            input_fingerprint=HEX,
            ordering_policy_id="abs_gap_desc_instrument_key_asc_id_asc",
            selection_policy_id="two_bars_by_close_time_v1",
        ),
    )


def _cat(key: str, *, known_at: datetime | None = None) -> CatalystCollection:
    record = CatalystRecord(
        catalyst_record_id="2" * 64,
        source_event_id="e",
        source_content_fingerprint=HEX,
        instrument_key=key,
        local_symbol="X",
        catalyst_type="earnings",
        event_time=AS_OF - timedelta(hours=2),
        known_at=known_at or (AS_OF - timedelta(hours=1)),
        as_of=AS_OF,
        source_provider="fixture",
        rule_id="r",
    )
    return CatalystCollection(
        as_of=AS_OF,
        records=(record,),
        provenance=CatalystProvenance(
            config_fingerprint=HEX,
            input_fingerprint=HEX,
            ordering_policy_id="known_at_asc_event_time_asc_type_asc_instrument_key_asc_id_asc",
        ),
    )


def _score(key: str) -> ScoreCollection:
    record = ScoreRecord(
        score_record_id="3" * 64,
        instrument_key=key,
        local_symbol="X",
        score=Decimal("0.2"),
        components=ScoreComponents(watchlist_rank=Decimal("1")),
        policy_version_id="premarket.scoring.policy.v1",
        weight_profile_id="default_v1",
        as_of=AS_OF,
        watchlist_rank=1,
        watchlist_rule_id="r",
    )
    return ScoreCollection(
        as_of=AS_OF,
        records=(record,),
        provenance=ScoreProvenance(
            config_fingerprint=HEX,
            input_fingerprint=HEX,
            ordering_policy_id="score_desc_instrument_key_asc_score_record_id_asc",
            policy_version_id="premarket.scoring.policy.v1",
            weight_profile_id="default_v1",
        ),
    )


def test_missing_catalysts_insufficient_with_absence_marker() -> None:
    key = "bergama:equity:us:aapl"
    artifact = project_analyst(
        AnalystProjectionRequest(
            as_of=AS_OF,
            watchlist=_wl(key),
            gaps=_gap(key),
            catalysts=None,
            scores=_score(key),
        )
    )
    assert artifact.evaluation_state == "INSUFFICIENT_EVIDENCE"
    assert artifact.catalyst_summary.absence_marker is True
    assert artifact.catalyst_summary.unavailable_marker is True


def test_empty_gap_collection_insufficient() -> None:
    key = "bergama:equity:us:aapl"
    empty = GapCollection(
        as_of=AS_OF,
        records=(),
        provenance=GapProvenance(
            config_fingerprint=HEX,
            input_fingerprint=HEX,
            ordering_policy_id="abs_gap_desc_instrument_key_asc_id_asc",
            selection_policy_id="two_bars_by_close_time_v1",
        ),
    )
    artifact = project_analyst(
        AnalystProjectionRequest(
            as_of=AS_OF,
            watchlist=_wl(key),
            gaps=empty,
            catalysts=_cat(key),
            scores=_score(key),
        )
    )
    assert artifact.evaluation_state == "INSUFFICIENT_EVIDENCE"


def test_unsupported_security_not_evaluable() -> None:
    key = "bergama:equity:us:aapl"
    artifact = project_analyst(
        AnalystProjectionRequest(
            as_of=AS_OF,
            watchlist=_wl(key),
            gaps=_gap(key),
            catalysts=_cat(key),
            scores=_score(key),
            unsupported_instrument_keys=(key,),
        )
    )
    assert artifact.evaluation_state == "NOT_EVALUABLE"
    assert any(flag.category == "UNSUPPORTED_EVALUATION" for flag in artifact.risk_flags)


def test_empty_watchlist_not_evaluable() -> None:
    empty_wl = Watchlist(
        evaluation_timestamp=AS_OF,
        entries=(),
        provenance=WatchlistProvenance(
            config_fingerprint=HEX,
            input_fingerprint=HEX,
            ordering_policy_id="rule_priority_asc_instrument_key_asc",
        ),
    )
    artifact = project_analyst(
        AnalystProjectionRequest(
            as_of=AS_OF,
            watchlist=empty_wl,
            gaps=_gap("bergama:equity:us:aapl"),
            catalysts=_cat("bergama:equity:us:aapl"),
            scores=_score("bergama:equity:us:aapl"),
        )
    )
    assert artifact.evaluation_state == "NOT_EVALUABLE"


def test_stale_gap_known_at_maps_not_evaluable() -> None:
    key = "bergama:equity:us:aapl"
    artifact = project_analyst(
        AnalystProjectionRequest(
            as_of=AS_OF,
            watchlist=_wl(key),
            gaps=_gap(key, known_at=AS_OF + timedelta(seconds=1)),
            catalysts=_cat(key),
            scores=_score(key),
        )
    )
    assert artifact.evaluation_state == "NOT_EVALUABLE"
    assert any(flag.category == "STALE_DATA" for flag in artifact.risk_flags)
