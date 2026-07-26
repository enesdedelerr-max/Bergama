"""Contract tests for Premarket Watchlist Engine (#72)."""

from __future__ import annotations

from datetime import UTC, datetime

import bergama_strategy_sdk
from app.market_data.events.bar import BarEvent
from app.market_data.identity import InstrumentId
from app.premarket import __all__ as premarket_all
from app.premarket.watchlist.engine import generate_watchlist
from app.premarket.watchlist.models import (
    Watchlist,
    WatchlistCandidate,
    WatchlistConfig,
    WatchlistEntry,
    WatchlistGenerationRequest,
    WatchlistInclusionRule,
    WatchlistProvenance,
)
from app.premarket.watchlist.ordering import ORDERING_POLICY_RULE_PRIORITY_ASC_INSTRUMENT_KEY_ASC
from tests.contract.test_strategy_sdk_contract import FROZEN_PUBLIC_API


def test_watchlist_models_are_frozen_and_forbid_extra() -> None:
    for model in (
        WatchlistCandidate,
        WatchlistInclusionRule,
        WatchlistConfig,
        WatchlistGenerationRequest,
        WatchlistEntry,
        WatchlistProvenance,
        Watchlist,
    ):
        assert model.model_config.get("frozen") is True
        assert model.model_config.get("extra") == "forbid"


def test_watchlist_output_contract_fields() -> None:
    as_of = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
    result = generate_watchlist(
        WatchlistGenerationRequest(
            candidates=(WatchlistCandidate(instrument_key="bergama:equity:us:aapl"),),
            as_of=as_of,
            config=WatchlistConfig(
                rules=(
                    WatchlistInclusionRule(
                        rule_id="allowlist",
                        rule_priority=1,
                        inclusion_reason="core",
                        allowed_instrument_keys=("bergama:equity:us:aapl",),
                    ),
                )
            ),
        )
    )
    entry = result.entries[0]
    assert set(WatchlistEntry.model_fields) >= {
        "instrument_key",
        "local_symbol",
        "evaluation_timestamp",
        "rank",
        "inclusion_reason",
        "rule_id",
    }
    assert set(WatchlistProvenance.model_fields) >= {
        "config_fingerprint",
        "input_fingerprint",
        "ordering_policy_id",
        "source_identifiers",
    }
    assert entry.rank == 1
    assert (
        result.provenance.ordering_policy_id == ORDERING_POLICY_RULE_PRIORITY_ASC_INSTRUMENT_KEY_ASC
    )
    assert len(result.provenance.config_fingerprint) == 64
    assert len(result.provenance.input_fingerprint) == 64


def test_premarket_public_surface_does_not_leak_into_strategy_sdk() -> None:
    assert tuple(bergama_strategy_sdk.__all__) == FROZEN_PUBLIC_API
    sdk_public = set(bergama_strategy_sdk.__all__)
    for symbol in premarket_all:
        assert symbol not in sdk_public


def test_market_data_bar_event_contract_unchanged_by_premarket_import() -> None:
    fields = set(BarEvent.model_fields)
    assert "close_time" in fields
    assert "open" in fields
    assert "instrument" in fields
    assert InstrumentId.model_fields["instrument_key"] is not None
