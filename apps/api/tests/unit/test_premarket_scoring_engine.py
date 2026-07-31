"""Unit tests for Premarket Scoring Engine (Policy Version v1) — hardened suite."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from types import MappingProxyType

import pytest
from app.core.premarket_settings import PremarketSettings
from app.market_data.money import canonical_decimal_str
from app.premarket.catalyst.models import (
    CatalystCollection,
    CatalystProvenance,
    CatalystRecord,
)
from app.premarket.catalyst.ordering import (
    ORDERING_POLICY_KNOWN_AT_ASC_EVENT_TIME_ASC_TYPE_ASC_INSTRUMENT_KEY_ASC_ID_ASC,
)
from app.premarket.errors import (
    PremarketDisabledError,
    ScoreConflictError,
    ScoreDuplicateInstrumentError,
    ScoreStaleKnownAtError,
    ScoreUnsupportedPolicyError,
    ScoreValidationError,
)
from app.premarket.gap.engine import scan_gaps
from app.premarket.gap.models import (
    GapCollection,
    GapConfig,
    GapProvenance,
    GapRecord,
    GapScanRequest,
)
from app.premarket.gap.ordering import ORDERING_POLICY_ABS_GAP_DESC_INSTRUMENT_KEY_ASC_ID_ASC
from app.premarket.gap.policy import (
    GAP_DIRECTION_DOWN,
    GAP_DIRECTION_UP,
    SELECTION_POLICY_TWO_BARS_BY_CLOSE_TIME_V1,
)
from app.premarket.scoring.aggregate import aggregate_terms
from app.premarket.scoring.engine import scan_scores, scan_scores_from_parts
from app.premarket.scoring.models import ScoreComponents, ScoreConfig, ScoreRequest
from app.premarket.scoring.normalize import quantize_unit_component
from app.premarket.scoring.ordering import order_score_drafts
from app.premarket.scoring.policy import (
    FEATURE_CATALYST_PRESENCE,
    FEATURE_GAP_MAGNITUDE,
    FEATURE_WATCHLIST_RANK,
    IDENTITY_SPECIFICATION_V1,
    ORDERING_POLICY_SCORE_DESC_INSTRUMENT_KEY_ASC_ID_ASC,
    POLICY_VERSION_V1,
    SCORE_QUANTUM,
    WEIGHT_PROFILE_DEFAULT_V1,
)
from app.premarket.scoring.policy_v1.weight_profile_default_v1 import (
    build_default_v1_weight_profile,
)
from app.premarket.scoring.ports import ScoreRecordDraft, WeightedTerm, WeightedTerms
from app.premarket.scoring.replay import assert_replay_equal, rescore
from app.premarket.scoring.resolve_policy import (
    override_binder_registry,
    registered_policy_version_ids,
    reset_binder_registry,
    resolve_policy,
)
from app.premarket.watchlist.models import Watchlist, WatchlistEntry, WatchlistProvenance
from app.strategy.keys import strategy_sha256
from pydantic import ValidationError
from tests.support.market_data_fixtures import instrument, make_bar, source

AS_OF = datetime(2026, 7, 17, 14, 0, 0, tzinfo=UTC)
DAY1 = datetime(2026, 7, 15, 20, 0, 0, tzinfo=UTC)
DAY2 = datetime(2026, 7, 16, 20, 0, 0, tzinfo=UTC)
HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64
HEX_D = "d" * 64
HEX_E = "e" * 64


def _watchlist(
    *keys: tuple[str, str | None],
    ranks: tuple[int, ...] | None = None,
) -> Watchlist:
    entries = tuple(
        WatchlistEntry(
            instrument_key=key,
            local_symbol=symbol,
            evaluation_timestamp=AS_OF,
            rank=(ranks[index] if ranks is not None else index + 1),
            inclusion_reason="core",
            rule_id="allowlist",
        )
        for index, (key, symbol) in enumerate(keys)
    )
    return Watchlist(
        evaluation_timestamp=AS_OF,
        entries=entries,
        provenance=WatchlistProvenance(
            config_fingerprint=HEX_A,
            input_fingerprint=HEX_B,
            ordering_policy_id="rule_priority_asc_instrument_key_asc",
            source_identifiers=tuple(entry.instrument_key for entry in entries),
        ),
    )


def _watchlist_model_construct(
    *entries: WatchlistEntry,
) -> Watchlist:
    return Watchlist.model_construct(
        evaluation_timestamp=AS_OF,
        entries=entries,
        provenance=WatchlistProvenance(
            config_fingerprint=HEX_A,
            input_fingerprint=HEX_B,
            ordering_policy_id="rule_priority_asc_instrument_key_asc",
            source_identifiers=tuple(entry.instrument_key for entry in entries),
        ),
    )


def _bar(
    *,
    instrument_key: str,
    close_time: datetime,
    open_price: str,
    close_price: str,
    source_event_id: str,
    known_at: datetime | None = None,
    local_symbol: str = "SYM",
):
    known = known_at or (close_time + timedelta(minutes=1))
    return make_bar(
        instrument=instrument(instrument_key=instrument_key, local_symbol=local_symbol),
        source=source(provider="fixture", source_event_id=source_event_id),
        occurred_at=close_time,
        effective_at=close_time,
        known_at=known,
        ingested_at=known + timedelta(seconds=1),
        window_start=close_time - timedelta(hours=24),
        window_end=close_time,
        close_time=close_time,
        open=Decimal(open_price),
        high=Decimal(close_price) + Decimal("1"),
        low=Decimal(open_price) - Decimal("1"),
        close=Decimal(close_price),
        volume=Decimal("1000"),
    )


def _gaps_for(watchlist: Watchlist, *, open_map: dict[str, str]) -> GapCollection:
    bars = []
    for entry in watchlist.entries:
        bars.append(
            _bar(
                instrument_key=entry.instrument_key,
                close_time=DAY1,
                open_price="100",
                close_price="100",
                source_event_id=f"{entry.instrument_key}-d1",
                local_symbol=entry.local_symbol or "SYM",
            )
        )
        bars.append(
            _bar(
                instrument_key=entry.instrument_key,
                close_time=DAY2,
                open_price=open_map[entry.instrument_key],
                close_price=open_map[entry.instrument_key],
                source_event_id=f"{entry.instrument_key}-d2",
                local_symbol=entry.local_symbol or "SYM",
            )
        )
    result = scan_gaps(
        GapScanRequest(
            watchlist=watchlist,
            bars=tuple(bars),
            as_of=AS_OF,
            config=GapConfig(),
        )
    )
    assert isinstance(result, GapCollection)
    return result


def _manual_gap(
    *,
    gap_record_id: str,
    instrument_key: str,
    gap_percent: Decimal | str,
    known_at: datetime | None = None,
    direction: str = GAP_DIRECTION_UP,
) -> GapRecord:
    percent = gap_percent if isinstance(gap_percent, Decimal) else Decimal(gap_percent)
    return GapRecord(
        gap_record_id=gap_record_id,
        instrument_key=instrument_key,
        local_symbol="AAPL",
        previous_session_close=Decimal("100"),
        current_session_open=Decimal("100") + percent * Decimal("100"),
        gap_percent=percent,
        gap_direction=direction,
        event_time=DAY2,
        known_at=known_at or (DAY2 + timedelta(minutes=1)),
        as_of=AS_OF,
        selection_policy_id=SELECTION_POLICY_TWO_BARS_BY_CLOSE_TIME_V1,
        previous_bar_source_event_id="prev",
        current_bar_source_event_id="curr",
    )


def _gap_collection(*records: GapRecord, as_of: datetime = AS_OF) -> GapCollection:
    return GapCollection(
        as_of=as_of,
        records=records,
        provenance=GapProvenance(
            config_fingerprint=HEX_A,
            input_fingerprint=HEX_B,
            ordering_policy_id=ORDERING_POLICY_ABS_GAP_DESC_INSTRUMENT_KEY_ASC_ID_ASC,
            selection_policy_id=SELECTION_POLICY_TWO_BARS_BY_CLOSE_TIME_V1,
            source_identifiers=tuple(record.gap_record_id for record in records),
        ),
    )


def _catalyst(
    *,
    catalyst_record_id: str,
    instrument_key: str,
    known_at: datetime | None = None,
    catalyst_type: str = "earnings",
) -> CatalystRecord:
    return CatalystRecord(
        catalyst_record_id=catalyst_record_id,
        source_event_id="news-1",
        source_content_fingerprint=catalyst_record_id,
        instrument_key=instrument_key,
        local_symbol="AAPL",
        catalyst_type=catalyst_type,
        event_time=AS_OF - timedelta(hours=1),
        known_at=known_at or (AS_OF - timedelta(minutes=30)),
        as_of=AS_OF,
        source_provider="fixture",
        rule_id="earnings-topic",
    )


def _catalyst_collection(*records: CatalystRecord, as_of: datetime = AS_OF) -> CatalystCollection:
    return CatalystCollection(
        as_of=as_of,
        records=records,
        provenance=CatalystProvenance(
            config_fingerprint=HEX_A,
            input_fingerprint=HEX_B,
            ordering_policy_id=(
                ORDERING_POLICY_KNOWN_AT_ASC_EVENT_TIME_ASC_TYPE_ASC_INSTRUMENT_KEY_ASC_ID_ASC
            ),
            source_identifiers=tuple(record.catalyst_record_id for record in records),
        ),
    )


def _expected_identity(
    *,
    instrument_key: str,
    score: Decimal,
    watchlist_rank_component: Decimal,
    watchlist_rank: int,
    gap_magnitude: Decimal | None = None,
    catalyst_presence: Decimal | None = None,
    gap_record_id: str = "",
    catalyst_source_identifiers: tuple[str, ...] = (),
    as_of: datetime = AS_OF,
    rule_id: str = "allowlist",
) -> str:
    """Independently derive score_record_id from the documented Identity Spec payload."""
    payload = {
        "schema": IDENTITY_SPECIFICATION_V1,
        "policy_version_id": POLICY_VERSION_V1,
        "weight_profile_id": WEIGHT_PROFILE_DEFAULT_V1,
        "instrument_key": instrument_key,
        "as_of": as_of,
        "score": canonical_decimal_str(score),
        "components": {
            "watchlist_rank": canonical_decimal_str(watchlist_rank_component),
            "gap_magnitude": (
                None if gap_magnitude is None else canonical_decimal_str(gap_magnitude)
            ),
            "catalyst_presence": (
                None if catalyst_presence is None else canonical_decimal_str(catalyst_presence)
            ),
        },
        "watchlist_rank": watchlist_rank,
        "watchlist_rule_id": rule_id,
        "gap_record_id": gap_record_id,
        "catalyst_source_identifiers": list(catalyst_source_identifiers),
    }
    return strategy_sha256(payload)


def _draft(
    *,
    score_record_id: str,
    instrument_key: str,
    score: str,
) -> ScoreRecordDraft:
    return ScoreRecordDraft(
        score_record_id=score_record_id,
        instrument_key=instrument_key,
        local_symbol=None,
        score=Decimal(score),
        components=ScoreComponents(watchlist_rank=Decimal("1.00000000")),
        policy_version_id=POLICY_VERSION_V1,
        weight_profile_id=WEIGHT_PROFILE_DEFAULT_V1,
        as_of=AS_OF,
        watchlist_rank=1,
        watchlist_rule_id="allowlist",
        gap_record_id=None,
        catalyst_source_identifiers=(),
        source_identifiers=(),
    )


# ---------------------------------------------------------------------------
# Public component domain
# ---------------------------------------------------------------------------


def test_component_boundaries_accepted() -> None:
    assert ScoreComponents(watchlist_rank=Decimal("0")).watchlist_rank == Decimal("0")
    assert ScoreComponents(watchlist_rank=Decimal("1")).watchlist_rank == Decimal("1")
    assert (
        ScoreComponents(
            watchlist_rank=Decimal("1"),
            gap_magnitude=None,
            catalyst_presence=None,
        ).gap_magnitude
        is None
    )


def test_component_out_of_domain_rejected() -> None:
    with pytest.raises(ValidationError):
        ScoreComponents(watchlist_rank=Decimal("-0.00000001"))
    with pytest.raises(ValidationError):
        ScoreComponents(watchlist_rank=Decimal("1.00000001"))
    with pytest.raises(ValidationError):
        ScoreComponents(watchlist_rank=Decimal("NaN"))
    with pytest.raises(ValidationError):
        ScoreComponents(watchlist_rank=Decimal("Infinity"))
    with pytest.raises(ValidationError):
        ScoreComponents(watchlist_rank=Decimal("-Infinity"))


def test_required_watchlist_component_null_rejected() -> None:
    with pytest.raises(ValidationError):
        ScoreComponents.model_validate({"watchlist_rank": None})


# ---------------------------------------------------------------------------
# Core formulas / combinations
# ---------------------------------------------------------------------------


def test_settings_disabled_fail_closed() -> None:
    with pytest.raises(PremarketDisabledError):
        scan_scores_from_parts(
            watchlist=_watchlist(("bergama:equity:us:aapl", "AAPL")),
            as_of=AS_OF,
            settings=PremarketSettings(enabled=False),
        )


def test_watchlist_only() -> None:
    result = scan_scores(
        ScoreRequest(
            watchlist=_watchlist(
                ("bergama:equity:us:aapl", "AAPL"),
                ("bergama:equity:us:msft", "MSFT"),
            ),
            as_of=AS_OF,
            config=ScoreConfig(),
        )
    )
    assert result.records[0].score == Decimal("0.50000000")
    assert result.records[1].score == Decimal("0.25000000")
    assert result.records[0].components.gap_magnitude is None
    assert result.records[0].components.catalyst_presence is None


def test_weight_non_redistribution() -> None:
    result = scan_scores(
        ScoreRequest(
            watchlist=_watchlist(("bergama:equity:us:aapl", "AAPL")),
            as_of=AS_OF,
            config=ScoreConfig(),
        )
    )
    assert result.records[0].score == Decimal("0.50000000")


def test_watchlist_plus_gap() -> None:
    watchlist = _watchlist(("bergama:equity:us:aapl", "AAPL"))
    gaps = _gap_collection(
        _manual_gap(
            gap_record_id=HEX_C,
            instrument_key="bergama:equity:us:aapl",
            gap_percent="0.10",
        )
    )
    result = scan_scores(
        ScoreRequest(watchlist=watchlist, as_of=AS_OF, config=ScoreConfig(), gaps=gaps)
    )
    assert result.records[0].components.gap_magnitude == Decimal("1.00000000")
    assert result.records[0].score == Decimal("0.80000000")


def test_watchlist_plus_catalyst() -> None:
    result = scan_scores(
        ScoreRequest(
            watchlist=_watchlist(("bergama:equity:us:aapl", "AAPL")),
            as_of=AS_OF,
            config=ScoreConfig(),
            catalysts=_catalyst_collection(
                _catalyst(catalyst_record_id=HEX_C, instrument_key="bergama:equity:us:aapl")
            ),
        )
    )
    assert result.records[0].components.catalyst_presence == Decimal("1.00000000")
    assert result.records[0].score == Decimal("0.70000000")


def test_watchlist_gap_and_catalyst() -> None:
    result = scan_scores(
        ScoreRequest(
            watchlist=_watchlist(("bergama:equity:us:aapl", "AAPL")),
            as_of=AS_OF,
            config=ScoreConfig(),
            gaps=_gap_collection(
                _manual_gap(
                    gap_record_id=HEX_C,
                    instrument_key="bergama:equity:us:aapl",
                    gap_percent="0.10",
                )
            ),
            catalysts=_catalyst_collection(
                _catalyst(catalyst_record_id=HEX_D, instrument_key="bergama:equity:us:aapl")
            ),
        )
    )
    assert result.records[0].score == Decimal("1.00000000")


# ---------------------------------------------------------------------------
# Rank validation
# ---------------------------------------------------------------------------


def test_rank_zero_fail_closed_at_scoring_boundary() -> None:
    entry = WatchlistEntry.model_construct(
        instrument_key="bergama:equity:us:aapl",
        local_symbol="AAPL",
        evaluation_timestamp=AS_OF,
        rank=0,
        inclusion_reason="core",
        rule_id="allowlist",
    )
    with pytest.raises(ScoreValidationError) as exc_info:
        scan_scores(
            ScoreRequest(
                watchlist=_watchlist_model_construct(entry),
                as_of=AS_OF,
                config=ScoreConfig(),
            )
        )
    assert "invalid_rank" in str(exc_info.value.detail)


def test_rank_exceeds_universe_fail_closed() -> None:
    entry = WatchlistEntry.model_construct(
        instrument_key="bergama:equity:us:aapl",
        local_symbol="AAPL",
        evaluation_timestamp=AS_OF,
        rank=2,
        inclusion_reason="core",
        rule_id="allowlist",
    )
    with pytest.raises(ScoreValidationError) as exc_info:
        scan_scores(
            ScoreRequest(
                watchlist=_watchlist_model_construct(entry),
                as_of=AS_OF,
                config=ScoreConfig(),
            )
        )
    assert "rank_exceeds_universe" in str(exc_info.value.detail)


def test_rank_n_equals_one_and_first_last() -> None:
    single = scan_scores(
        ScoreRequest(
            watchlist=_watchlist(("bergama:equity:us:aapl", "AAPL")),
            as_of=AS_OF,
            config=ScoreConfig(),
        )
    )
    assert single.records[0].score == Decimal("0.50000000")
    multi = scan_scores(
        ScoreRequest(
            watchlist=_watchlist(
                ("bergama:equity:us:aapl", "AAPL"),
                ("bergama:equity:us:msft", "MSFT"),
            ),
            as_of=AS_OF,
            config=ScoreConfig(),
        )
    )
    assert multi.records[0].watchlist_rank == 1
    assert multi.records[1].watchlist_rank == 2
    assert multi.records[1].score == Decimal("0.25000000")


def test_duplicate_ranks_legal_across_instruments() -> None:
    result = scan_scores(
        ScoreRequest(
            watchlist=_watchlist(
                ("bergama:equity:us:msft", "MSFT"),
                ("bergama:equity:us:aapl", "AAPL"),
                ranks=(1, 1),
            ),
            as_of=AS_OF,
            config=ScoreConfig(),
        )
    )
    assert result.records[0].score == result.records[1].score == Decimal("0.50000000")
    assert result.records[0].instrument_key == "bergama:equity:us:aapl"


# ---------------------------------------------------------------------------
# Gap numeric edge cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("gap_percent", "direction", "expected_component", "expected_score"),
    [
        (Decimal("0"), GAP_DIRECTION_UP, Decimal("0E-8"), Decimal("0.50000000")),
        (Decimal("-0"), GAP_DIRECTION_DOWN, Decimal("0E-8"), Decimal("0.50000000")),
        (Decimal("0.05"), GAP_DIRECTION_UP, Decimal("0.50000000"), Decimal("0.65000000")),
        (Decimal("-0.05"), GAP_DIRECTION_DOWN, Decimal("0.50000000"), Decimal("0.65000000")),
        (Decimal("0.10"), GAP_DIRECTION_UP, Decimal("1.00000000"), Decimal("0.80000000")),
        (Decimal("0.09999999"), GAP_DIRECTION_UP, Decimal("0.99999990"), Decimal("0.79999997")),
        (Decimal("0.10000001"), GAP_DIRECTION_UP, Decimal("1.00000000"), Decimal("0.80000000")),
        (Decimal("1E-20"), GAP_DIRECTION_UP, Decimal("0E-8"), Decimal("0.50000000")),
        (Decimal("1E+3"), GAP_DIRECTION_UP, Decimal("1.00000000"), Decimal("0.80000000")),
        (Decimal("5E-2"), GAP_DIRECTION_UP, Decimal("0.50000000"), Decimal("0.65000000")),
    ],
)
def test_gap_numeric_matrix(
    gap_percent: Decimal,
    direction: str,
    expected_component: Decimal,
    expected_score: Decimal,
) -> None:
    result = scan_scores(
        ScoreRequest(
            watchlist=_watchlist(("bergama:equity:us:aapl", "AAPL")),
            as_of=AS_OF,
            config=ScoreConfig(),
            gaps=_gap_collection(
                _manual_gap(
                    gap_record_id=HEX_C,
                    instrument_key="bergama:equity:us:aapl",
                    gap_percent=gap_percent,
                    direction=direction,
                )
            ),
        )
    )
    assert result.records[0].components.gap_magnitude == expected_component
    assert result.records[0].score == expected_score


def test_half_even_quantize_boundary() -> None:
    # 0.000000015 quantizes to 0.00000002 under ROUND_HALF_EVEN (odd→even at 8dp).
    value = Decimal("0.000000015")
    assert value.quantize(SCORE_QUANTUM, rounding=ROUND_HALF_EVEN) == Decimal("0.00000002")
    assert quantize_unit_component(value, field_name="x") == Decimal("0.00000002")


def test_raw_weighted_sum_exactly_zero_and_one() -> None:
    zero_terms = WeightedTerms(
        instrument_key="bergama:equity:us:aapl",
        local_symbol="AAPL",
        terms=(
            WeightedTerm(
                feature_id=FEATURE_WATCHLIST_RANK,
                value=Decimal("0"),
                weight=Decimal("0.50"),
                contribution=Decimal("0"),
                present=True,
                watchlist_rank=1,
                watchlist_rule_id="allowlist",
            ),
            WeightedTerm(
                feature_id=FEATURE_GAP_MAGNITUDE,
                value=Decimal("0"),
                weight=Decimal("0.30"),
                contribution=Decimal("0"),
                present=False,
            ),
            WeightedTerm(
                feature_id=FEATURE_CATALYST_PRESENCE,
                value=Decimal("0"),
                weight=Decimal("0.20"),
                contribution=Decimal("0"),
                present=False,
            ),
        ),
    )
    from app.premarket.scoring.policy_v1.params import build_policy_v1_params

    params = build_policy_v1_params()
    zero = aggregate_terms(zero_terms, params=params)
    assert zero.score == Decimal("0.00000000")

    one_terms = WeightedTerms(
        instrument_key="bergama:equity:us:aapl",
        local_symbol="AAPL",
        terms=(
            WeightedTerm(
                feature_id=FEATURE_WATCHLIST_RANK,
                value=Decimal("1"),
                weight=Decimal("0.50"),
                contribution=Decimal("0.50"),
                present=True,
                watchlist_rank=1,
                watchlist_rule_id="allowlist",
                source_identifiers=("bergama:equity:us:aapl",),
            ),
            WeightedTerm(
                feature_id=FEATURE_GAP_MAGNITUDE,
                value=Decimal("1"),
                weight=Decimal("0.30"),
                contribution=Decimal("0.30"),
                present=True,
                gap_record_id=HEX_C,
                source_identifiers=(HEX_C,),
            ),
            WeightedTerm(
                feature_id=FEATURE_CATALYST_PRESENCE,
                value=Decimal("1"),
                weight=Decimal("0.20"),
                contribution=Decimal("0.20"),
                present=True,
                source_identifiers=(HEX_D,),
            ),
        ),
    )
    one = aggregate_terms(one_terms, params=params)
    assert one.score == Decimal("1.00000000")


def test_no_float_or_wall_clock_in_scoring_sources() -> None:
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "app" / "premarket" / "scoring"
    forbidden = re.compile(r"\bfloat\(|datetime\.now|utcnow|time\.time|uuid4|secrets\.|random\.")
    hits = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if forbidden.search(text):
            hits.append(str(path))
    assert hits == []


# ---------------------------------------------------------------------------
# Input combinations / empty collections
# ---------------------------------------------------------------------------


def test_empty_watchlist_variants() -> None:
    empty = _watchlist()
    omitted = scan_scores(ScoreRequest(watchlist=empty, as_of=AS_OF, config=ScoreConfig()))
    assert omitted.records == ()
    with_empty = scan_scores(
        ScoreRequest(
            watchlist=empty,
            as_of=AS_OF,
            config=ScoreConfig(),
            gaps=_gap_collection(),
            catalysts=_catalyst_collection(),
        )
    )
    assert with_empty.records == ()
    with_nonempty = scan_scores(
        ScoreRequest(
            watchlist=empty,
            as_of=AS_OF,
            config=ScoreConfig(),
            gaps=_gap_collection(
                _manual_gap(
                    gap_record_id=HEX_C,
                    instrument_key="bergama:equity:us:aapl",
                    gap_percent="0.10",
                )
            ),
            catalysts=_catalyst_collection(
                _catalyst(catalyst_record_id=HEX_D, instrument_key="bergama:equity:us:aapl")
            ),
        )
    )
    assert with_nonempty.records == ()


def test_optional_collections_empty_or_unmatched() -> None:
    watchlist = _watchlist(("bergama:equity:us:aapl", "AAPL"))
    empty_gap = scan_scores(
        ScoreRequest(
            watchlist=watchlist,
            as_of=AS_OF,
            config=ScoreConfig(),
            gaps=_gap_collection(),
        )
    )
    assert empty_gap.records[0].components.gap_magnitude is None
    assert empty_gap.records[0].score == Decimal("0.50000000")

    unmatched_gap = scan_scores(
        ScoreRequest(
            watchlist=watchlist,
            as_of=AS_OF,
            config=ScoreConfig(),
            gaps=_gap_collection(
                _manual_gap(
                    gap_record_id=HEX_C,
                    instrument_key="bergama:equity:us:msft",
                    gap_percent="0.10",
                )
            ),
        )
    )
    assert unmatched_gap.records[0].components.gap_magnitude is None
    assert unmatched_gap.records[0].score == Decimal("0.50000000")

    empty_cat = scan_scores(
        ScoreRequest(
            watchlist=watchlist,
            as_of=AS_OF,
            config=ScoreConfig(),
            catalysts=_catalyst_collection(),
        )
    )
    assert empty_cat.records[0].components.catalyst_presence == Decimal("0E-8")
    assert empty_cat.records[0].score == Decimal("0.50000000")

    unmatched_cat = scan_scores(
        ScoreRequest(
            watchlist=watchlist,
            as_of=AS_OF,
            config=ScoreConfig(),
            catalysts=_catalyst_collection(
                _catalyst(catalyst_record_id=HEX_C, instrument_key="bergama:equity:us:msft")
            ),
        )
    )
    assert unmatched_cat.records[0].components.catalyst_presence == Decimal("0E-8")


def test_out_of_universe_evidence_does_not_change_score() -> None:
    watchlist = _watchlist(("bergama:equity:us:aapl", "AAPL"))
    baseline = scan_scores(ScoreRequest(watchlist=watchlist, as_of=AS_OF, config=ScoreConfig()))
    polluted = scan_scores(
        ScoreRequest(
            watchlist=watchlist,
            as_of=AS_OF,
            config=ScoreConfig(),
            gaps=_gap_collection(
                _manual_gap(
                    gap_record_id=HEX_C,
                    instrument_key="bergama:equity:us:zzz",
                    gap_percent="0.50",
                )
            ),
            catalysts=_catalyst_collection(
                _catalyst(catalyst_record_id=HEX_D, instrument_key="bergama:equity:us:zzz")
            ),
        )
    )
    assert polluted.records[0].score == baseline.records[0].score


def test_evaluation_scoped_gap_conflict_aborts_all_instruments() -> None:
    watchlist = _watchlist(
        ("bergama:equity:us:aapl", "AAPL"),
        ("bergama:equity:us:msft", "MSFT"),
    )
    with pytest.raises(ScoreConflictError):
        scan_scores(
            ScoreRequest(
                watchlist=watchlist,
                as_of=AS_OF,
                config=ScoreConfig(),
                gaps=_gap_collection(
                    _manual_gap(
                        gap_record_id=HEX_C,
                        instrument_key="bergama:equity:us:aapl",
                        gap_percent="0.05",
                    ),
                    _manual_gap(
                        gap_record_id=HEX_D,
                        instrument_key="bergama:equity:us:aapl",
                        gap_percent="0.08",
                    ),
                    _manual_gap(
                        gap_record_id=HEX_E,
                        instrument_key="bergama:equity:us:msft",
                        gap_percent="0.10",
                    ),
                ),
            )
        )


# ---------------------------------------------------------------------------
# Catalyst identity canonicalization
# ---------------------------------------------------------------------------


def test_reversed_catalyst_order_identical_collection() -> None:
    watchlist = _watchlist(("bergama:equity:us:aapl", "AAPL"))
    forward = _catalyst_collection(
        _catalyst(catalyst_record_id=HEX_C, instrument_key="bergama:equity:us:aapl"),
        _catalyst(catalyst_record_id=HEX_D, instrument_key="bergama:equity:us:aapl"),
    )
    reverse = _catalyst_collection(
        _catalyst(catalyst_record_id=HEX_D, instrument_key="bergama:equity:us:aapl"),
        _catalyst(catalyst_record_id=HEX_C, instrument_key="bergama:equity:us:aapl"),
    )
    first = scan_scores(
        ScoreRequest(watchlist=watchlist, as_of=AS_OF, config=ScoreConfig(), catalysts=forward)
    )
    second = scan_scores(
        ScoreRequest(watchlist=watchlist, as_of=AS_OF, config=ScoreConfig(), catalysts=reverse)
    )
    assert first.model_dump(mode="python") == second.model_dump(mode="python")
    assert first.records[0].score_record_id == second.records[0].score_record_id
    assert first.provenance.input_fingerprint == second.provenance.input_fingerprint
    assert first.provenance.source_identifiers == second.provenance.source_identifiers
    assert first.records[0].catalyst_source_identifiers == (HEX_C, HEX_D)


def test_catalyst_set_change_changes_identity() -> None:
    watchlist = _watchlist(("bergama:equity:us:aapl", "AAPL"))
    one = scan_scores(
        ScoreRequest(
            watchlist=watchlist,
            as_of=AS_OF,
            config=ScoreConfig(),
            catalysts=_catalyst_collection(
                _catalyst(catalyst_record_id=HEX_C, instrument_key="bergama:equity:us:aapl")
            ),
        )
    )
    two = scan_scores(
        ScoreRequest(
            watchlist=watchlist,
            as_of=AS_OF,
            config=ScoreConfig(),
            catalysts=_catalyst_collection(
                _catalyst(catalyst_record_id=HEX_C, instrument_key="bergama:equity:us:aapl"),
                _catalyst(catalyst_record_id=HEX_D, instrument_key="bergama:equity:us:aapl"),
            ),
        )
    )
    assert one.records[0].score == two.records[0].score == Decimal("0.70000000")
    assert one.records[0].score_record_id != two.records[0].score_record_id
    assert one.provenance.input_fingerprint != two.provenance.input_fingerprint


def test_duplicate_equivalent_catalyst_collapses() -> None:
    watchlist = _watchlist(("bergama:equity:us:aapl", "AAPL"))
    duplicate = _catalyst(catalyst_record_id=HEX_C, instrument_key="bergama:equity:us:aapl")
    result = scan_scores(
        ScoreRequest(
            watchlist=watchlist,
            as_of=AS_OF,
            config=ScoreConfig(),
            catalysts=_catalyst_collection(duplicate, duplicate),
        )
    )
    assert result.records[0].catalyst_source_identifiers == (HEX_C,)
    assert result.records[0].components.catalyst_presence == Decimal("1.00000000")


def test_conflicting_catalyst_identity_fail_closed() -> None:
    watchlist = _watchlist(("bergama:equity:us:aapl", "AAPL"))
    first = _catalyst(catalyst_record_id=HEX_C, instrument_key="bergama:equity:us:aapl")
    conflict = first.model_copy(update={"catalyst_type": "guidance"})
    with pytest.raises(ScoreConflictError) as exc_info:
        scan_scores(
            ScoreRequest(
                watchlist=watchlist,
                as_of=AS_OF,
                config=ScoreConfig(),
                catalysts=_catalyst_collection(first, conflict),
            )
        )
    assert "conflicting_catalyst_identity" in str(exc_info.value.detail)


# ---------------------------------------------------------------------------
# PIT
# ---------------------------------------------------------------------------


def test_naive_as_of_rejected() -> None:
    with pytest.raises(ValidationError):
        ScoreRequest(
            watchlist=_watchlist(("bergama:equity:us:aapl", "AAPL")),
            as_of=datetime(2026, 7, 17, 14, 0, 0),
            config=ScoreConfig(),
        )


def test_utc_and_fixed_offset_as_of() -> None:
    watchlist = _watchlist(("bergama:equity:us:aapl", "AAPL"))
    utc = scan_scores(ScoreRequest(watchlist=watchlist, as_of=AS_OF, config=ScoreConfig()))
    offset = timezone(timedelta(hours=-4))
    offset_as_of = datetime(2026, 7, 17, 10, 0, 0, tzinfo=offset)
    request = ScoreRequest(watchlist=watchlist, as_of=offset_as_of, config=ScoreConfig())
    assert request.as_of == AS_OF
    assert utc.records[0].score == Decimal("0.50000000")


def test_known_at_equal_and_plus_one_microsecond() -> None:
    watchlist = _watchlist(("bergama:equity:us:aapl", "AAPL"))
    ok = scan_scores(
        ScoreRequest(
            watchlist=watchlist,
            as_of=AS_OF,
            config=ScoreConfig(),
            gaps=_gap_collection(
                _manual_gap(
                    gap_record_id=HEX_C,
                    instrument_key="bergama:equity:us:aapl",
                    gap_percent="0.05",
                    known_at=AS_OF,
                )
            ),
            catalysts=_catalyst_collection(
                _catalyst(
                    catalyst_record_id=HEX_D,
                    instrument_key="bergama:equity:us:aapl",
                    known_at=AS_OF,
                )
            ),
        )
    )
    assert ok.records[0].score == Decimal("0.85000000")
    with pytest.raises(ScoreStaleKnownAtError):
        scan_scores(
            ScoreRequest(
                watchlist=watchlist,
                as_of=AS_OF,
                config=ScoreConfig(),
                gaps=_gap_collection(
                    _manual_gap(
                        gap_record_id=HEX_C,
                        instrument_key="bergama:equity:us:aapl",
                        gap_percent="0.05",
                        known_at=AS_OF + timedelta(microseconds=1),
                    )
                ),
            )
        )
    with pytest.raises(ScoreStaleKnownAtError):
        scan_scores(
            ScoreRequest(
                watchlist=watchlist,
                as_of=AS_OF,
                config=ScoreConfig(),
                catalysts=_catalyst_collection(
                    _catalyst(
                        catalyst_record_id=HEX_D,
                        instrument_key="bergama:equity:us:aapl",
                        known_at=AS_OF + timedelta(microseconds=1),
                    )
                ),
            )
        )


def test_cross_pit_collection_mismatches() -> None:
    watchlist = _watchlist(("bergama:equity:us:aapl", "AAPL"))
    with pytest.raises(ScoreConflictError):
        scan_scores(
            ScoreRequest(
                watchlist=watchlist,
                as_of=AS_OF,
                config=ScoreConfig(),
                gaps=_gap_collection(
                    _manual_gap(
                        gap_record_id=HEX_C,
                        instrument_key="bergama:equity:us:aapl",
                        gap_percent="0.05",
                    ),
                    as_of=AS_OF + timedelta(seconds=1),
                ),
            )
        )
    with pytest.raises(ScoreConflictError):
        scan_scores(
            ScoreRequest(
                watchlist=watchlist,
                as_of=AS_OF,
                config=ScoreConfig(),
                catalysts=_catalyst_collection(
                    _catalyst(catalyst_record_id=HEX_D, instrument_key="bergama:equity:us:aapl"),
                    as_of=AS_OF + timedelta(seconds=1),
                ),
            )
        )


def test_empty_collection_as_of_mismatch_still_fail_closed() -> None:
    watchlist = _watchlist(("bergama:equity:us:aapl", "AAPL"))
    with pytest.raises(ScoreConflictError):
        scan_scores(
            ScoreRequest(
                watchlist=watchlist,
                as_of=AS_OF,
                config=ScoreConfig(),
                gaps=_gap_collection(as_of=AS_OF + timedelta(seconds=1)),
            )
        )


def test_replay_equality() -> None:
    request = ScoreRequest(
        watchlist=_watchlist(("bergama:equity:us:aapl", "AAPL")),
        as_of=AS_OF,
        config=ScoreConfig(),
    )
    assert_replay_equal(scan_scores(request), rescore(request))


# ---------------------------------------------------------------------------
# Identity / provenance goldens
# ---------------------------------------------------------------------------


def test_independent_golden_identity_and_sensitivity() -> None:
    watchlist = _watchlist(("bergama:equity:us:aapl", "AAPL"))
    request = ScoreRequest(watchlist=watchlist, as_of=AS_OF, config=ScoreConfig())
    result = scan_scores(request)
    expected = _expected_identity(
        instrument_key="bergama:equity:us:aapl",
        score=Decimal("0.50000000"),
        watchlist_rank_component=Decimal("1.00000000"),
        watchlist_rank=1,
    )
    assert result.records[0].score_record_id == expected

    changed_as_of = scan_scores(
        ScoreRequest(
            watchlist=watchlist,
            as_of=AS_OF + timedelta(seconds=1),
            config=ScoreConfig(),
        )
    )
    assert changed_as_of.records[0].score_record_id != expected

    other_instrument = scan_scores(
        ScoreRequest(
            watchlist=_watchlist(("bergama:equity:us:msft", "MSFT")),
            as_of=AS_OF,
            config=ScoreConfig(),
        )
    )
    assert other_instrument.records[0].score_record_id != expected

    with_gap = scan_scores(
        ScoreRequest(
            watchlist=watchlist,
            as_of=AS_OF,
            config=ScoreConfig(),
            gaps=_gap_collection(
                _manual_gap(
                    gap_record_id=HEX_C,
                    instrument_key="bergama:equity:us:aapl",
                    gap_percent="0.10",
                )
            ),
        )
    )
    assert with_gap.records[0].score_record_id == _expected_identity(
        instrument_key="bergama:equity:us:aapl",
        score=Decimal("0.80000000"),
        watchlist_rank_component=Decimal("1.00000000"),
        watchlist_rank=1,
        gap_magnitude=Decimal("1.00000000"),
        gap_record_id=HEX_C,
    )
    assert with_gap.records[0].score_record_id != expected

    with_catalyst = scan_scores(
        ScoreRequest(
            watchlist=watchlist,
            as_of=AS_OF,
            config=ScoreConfig(),
            catalysts=_catalyst_collection(
                _catalyst(catalyst_record_id=HEX_D, instrument_key="bergama:equity:us:aapl")
            ),
        )
    )
    assert with_catalyst.records[0].score_record_id == _expected_identity(
        instrument_key="bergama:equity:us:aapl",
        score=Decimal("0.70000000"),
        watchlist_rank_component=Decimal("1.00000000"),
        watchlist_rank=1,
        catalyst_presence=Decimal("1.00000000"),
        catalyst_source_identifiers=(HEX_D,),
    )


def test_empty_collection_provenance_stable() -> None:
    first = scan_scores(ScoreRequest(watchlist=_watchlist(), as_of=AS_OF, config=ScoreConfig()))
    second = scan_scores(ScoreRequest(watchlist=_watchlist(), as_of=AS_OF, config=ScoreConfig()))
    assert first.provenance.config_fingerprint == second.provenance.config_fingerprint
    assert first.provenance.input_fingerprint == second.provenance.input_fingerprint
    assert len(first.provenance.config_fingerprint) == 64


def test_deterministic_ordering_engine() -> None:
    drafts = [
        _draft(score_record_id=HEX_B, instrument_key="bergama:equity:us:msft", score="0.40"),
        _draft(score_record_id=HEX_A, instrument_key="bergama:equity:us:aapl", score="0.80"),
        _draft(score_record_id=HEX_D, instrument_key="bergama:equity:us:zzz", score="0.40"),
        _draft(score_record_id=HEX_C, instrument_key="bergama:equity:us:msft", score="0.40"),
    ]
    ordered = order_score_drafts(
        drafts,
        ordering_policy_id=ORDERING_POLICY_SCORE_DESC_INSTRUMENT_KEY_ASC_ID_ASC,
    )
    assert [item.score_record_id for item in ordered] == [HEX_A, HEX_B, HEX_C, HEX_D]


# ---------------------------------------------------------------------------
# Registry isolation / unsupported policies
# ---------------------------------------------------------------------------


def test_registry_override_restores_after_exception_and_success() -> None:
    config = ScoreConfig()
    assert POLICY_VERSION_V1 in registered_policy_version_ids()
    with pytest.raises(RuntimeError), override_binder_registry({}):
        with pytest.raises(ScoreUnsupportedPolicyError):
            resolve_policy(config)
        raise RuntimeError("boom")
    assert resolve_policy(config).params.policy_version_id == POLICY_VERSION_V1
    with override_binder_registry({}), pytest.raises(ScoreUnsupportedPolicyError):
        resolve_policy(config)
    assert resolve_policy(config).params.policy_version_id == POLICY_VERSION_V1
    reset_binder_registry()
    assert registered_policy_version_ids() == (POLICY_VERSION_V1,)


def test_unsupported_policy_and_ordering() -> None:
    with pytest.raises(ValidationError):
        ScoreConfig(policy_version_id="premarket.scoring.policy.v999")
    with pytest.raises(ValidationError):
        ScoreConfig(ordering_policy_id="score_asc_only")
    config = ScoreConfig.model_construct(
        policy_version_id="premarket.scoring.policy.v999",
        weight_profile_id=WEIGHT_PROFILE_DEFAULT_V1,
        ordering_policy_id=ORDERING_POLICY_SCORE_DESC_INSTRUMENT_KEY_ASC_ID_ASC,
        score_quantize_policy_id="decimal_8dp_half_even",
    )
    with pytest.raises(ScoreUnsupportedPolicyError):
        resolve_policy(config)
    with pytest.raises(ScoreUnsupportedPolicyError):
        order_score_drafts([], ordering_policy_id="score_asc_only")


def test_weight_profile_immutable() -> None:
    profile = build_default_v1_weight_profile()
    assert isinstance(profile.weights, MappingProxyType)
    with pytest.raises(TypeError):
        profile.weights["watchlist_rank"] = Decimal("1")  # type: ignore[index]


def test_duplicate_watchlist_instrument() -> None:
    entry = WatchlistEntry(
        instrument_key="bergama:equity:us:aapl",
        local_symbol="AAPL",
        evaluation_timestamp=AS_OF,
        rank=1,
        inclusion_reason="core",
        rule_id="allowlist",
    )
    watchlist = Watchlist(
        evaluation_timestamp=AS_OF,
        entries=(entry, entry.model_copy(update={"rank": 2})),
        provenance=WatchlistProvenance(
            config_fingerprint=HEX_A,
            input_fingerprint=HEX_B,
            ordering_policy_id="rule_priority_asc_instrument_key_asc",
            source_identifiers=("bergama:equity:us:aapl", "bergama:equity:us:aapl"),
        ),
    )
    with pytest.raises(ScoreDuplicateInstrumentError):
        scan_scores(ScoreRequest(watchlist=watchlist, as_of=AS_OF, config=ScoreConfig()))
