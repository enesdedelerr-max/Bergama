"""Contract tests for Premarket Scoring Foundation."""

from __future__ import annotations

from datetime import UTC, datetime

import bergama_strategy_sdk
from app.premarket import __all__ as premarket_all
from app.premarket.scoring.engine import scan_scores
from app.premarket.scoring.models import (
    ScoreCollection,
    ScoreConfig,
    ScoreProvenance,
    ScoreRecord,
    ScoreRequest,
)
from app.premarket.watchlist.models import Watchlist, WatchlistEntry, WatchlistProvenance
from tests.contract.test_strategy_sdk_contract import FROZEN_PUBLIC_API

AS_OF = datetime(2026, 7, 17, 14, 0, tzinfo=UTC)


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


def test_score_models_are_frozen_and_forbid_extra() -> None:
    for model in (ScoreConfig, ScoreRequest, ScoreRecord, ScoreProvenance, ScoreCollection):
        assert model.model_config.get("frozen") is True
        assert model.model_config.get("extra") == "forbid"


def test_score_output_contract_fields() -> None:
    result = scan_scores(ScoreRequest(watchlist=_watchlist(), as_of=AS_OF, config=ScoreConfig()))
    assert set(ScoreRecord.model_fields) >= {
        "score_record_id",
        "instrument_key",
        "score",
        "components",
        "policy_version_id",
        "weight_profile_id",
        "as_of",
    }
    assert set(ScoreProvenance.model_fields) >= {
        "config_fingerprint",
        "input_fingerprint",
        "ordering_policy_id",
        "policy_version_id",
        "weight_profile_id",
        "source_identifiers",
    }
    assert len(result.provenance.config_fingerprint) == 64


def test_premarket_scoring_surface_does_not_leak_into_strategy_sdk() -> None:
    assert tuple(bergama_strategy_sdk.__all__) == FROZEN_PUBLIC_API
    sdk_public = set(bergama_strategy_sdk.__all__)
    for symbol in premarket_all:
        assert symbol not in sdk_public
