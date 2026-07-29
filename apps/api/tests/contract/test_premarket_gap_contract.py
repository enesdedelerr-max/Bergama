"""Contract tests for Premarket Gap Scanner Foundation (#76)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import bergama_strategy_sdk
from app.market_data.events.bar import BarEvent
from app.market_data.identity import InstrumentId
from app.premarket import __all__ as premarket_all
from app.premarket.gap.engine import scan_gaps
from app.premarket.gap.models import (
    GapCollection,
    GapConfig,
    GapProvenance,
    GapRecord,
    GapScanRequest,
)
from app.premarket.gap.ordering import ORDERING_POLICY_ABS_GAP_DESC_INSTRUMENT_KEY_ASC_ID_ASC
from app.premarket.watchlist.models import Watchlist, WatchlistEntry, WatchlistProvenance
from tests.contract.test_strategy_sdk_contract import FROZEN_PUBLIC_API
from tests.support.market_data_fixtures import instrument, make_bar, source

AS_OF = datetime(2026, 7, 17, 14, 0, tzinfo=UTC)
DAY1 = datetime(2026, 7, 15, 20, 0, tzinfo=UTC)
DAY2 = datetime(2026, 7, 16, 20, 0, tzinfo=UTC)


def _watchlist() -> Watchlist:
    entry = WatchlistEntry(
        instrument_key="bergama:equity:us:aapl",
        local_symbol="AAPL",
        evaluation_timestamp=AS_OF,
        rank=1,
        inclusion_reason="core",
        rule_id="allowlist",
    )
    return Watchlist(
        evaluation_timestamp=AS_OF,
        entries=(entry,),
        provenance=WatchlistProvenance(
            config_fingerprint="a" * 64,
            input_fingerprint="b" * 64,
            ordering_policy_id="rule_priority_asc_instrument_key_asc",
            source_identifiers=("bergama:equity:us:aapl",),
        ),
    )


def _bar(close_time: datetime, open_price: str, close_price: str, source_event_id: str) -> BarEvent:
    known = close_time + timedelta(minutes=1)
    return make_bar(
        instrument=instrument(instrument_key="bergama:equity:us:aapl", local_symbol="AAPL"),
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


def test_gap_models_are_frozen_and_forbid_extra() -> None:
    for model in (GapConfig, GapScanRequest, GapRecord, GapProvenance, GapCollection):
        assert model.model_config.get("frozen") is True
        assert model.model_config.get("extra") == "forbid"


def test_gap_output_contract_fields() -> None:
    result = scan_gaps(
        GapScanRequest(
            watchlist=_watchlist(),
            bars=(
                _bar(DAY1, "100", "100", "d1"),
                _bar(DAY2, "105", "106", "d2"),
            ),
            as_of=AS_OF,
            config=GapConfig(),
        )
    )
    assert set(GapRecord.model_fields) >= {
        "gap_record_id",
        "instrument_key",
        "previous_session_close",
        "current_session_open",
        "gap_percent",
        "gap_direction",
        "event_time",
        "known_at",
        "as_of",
    }
    assert set(GapProvenance.model_fields) >= {
        "config_fingerprint",
        "input_fingerprint",
        "ordering_policy_id",
        "selection_policy_id",
        "source_identifiers",
    }
    assert (
        result.provenance.ordering_policy_id
        == ORDERING_POLICY_ABS_GAP_DESC_INSTRUMENT_KEY_ASC_ID_ASC
    )
    assert len(result.provenance.config_fingerprint) == 64


def test_premarket_gap_surface_does_not_leak_into_strategy_sdk() -> None:
    assert tuple(bergama_strategy_sdk.__all__) == FROZEN_PUBLIC_API
    sdk_public = set(bergama_strategy_sdk.__all__)
    for symbol in premarket_all:
        assert symbol not in sdk_public


def test_market_data_bar_contract_unchanged_by_gap_import() -> None:
    fields = set(BarEvent.model_fields)
    assert "open" in fields
    assert "close" in fields
    assert "close_time" in fields
    assert InstrumentId.model_fields["instrument_key"] is not None
