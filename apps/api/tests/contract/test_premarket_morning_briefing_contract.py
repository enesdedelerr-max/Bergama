"""Contract tests for Morning Briefing Foundation."""

from __future__ import annotations

from datetime import UTC, datetime

import bergama_strategy_sdk
import pytest
from app.premarket import __all__ as premarket_all
from app.premarket.morning_briefing.engine import assemble_briefing
from app.premarket.morning_briefing.models import (
    BriefingCollection,
    BriefingConfig,
    BriefingProvenance,
    BriefingRecord,
    BriefingRequest,
)
from app.premarket.scoring.engine import scan_scores
from app.premarket.scoring.models import ScoreConfig, ScoreRequest
from app.premarket.watchlist.models import Watchlist, WatchlistEntry, WatchlistProvenance
from tests.contract.test_strategy_sdk_contract import FROZEN_PUBLIC_API

AS_OF = datetime(2026, 7, 17, 14, 0, tzinfo=UTC)


def _scores():
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
    return scan_scores(ScoreRequest(watchlist=watchlist, as_of=AS_OF, config=ScoreConfig()))


def test_briefing_models_are_frozen_and_forbid_extra() -> None:
    for model in (
        BriefingConfig,
        BriefingRequest,
        BriefingRecord,
        BriefingProvenance,
        BriefingCollection,
    ):
        assert model.model_config.get("frozen") is True
        assert model.model_config.get("extra") == "forbid"


def test_briefing_output_contract_fields() -> None:
    result = assemble_briefing(
        BriefingRequest(scores=_scores(), as_of=AS_OF, config=BriefingConfig())
    )
    assert set(BriefingCollection.model_fields) >= {
        "briefing_id",
        "policy_version_id",
        "ordering_preservation_policy_id",
        "as_of",
        "records",
        "provenance",
    }
    assert set(BriefingRecord.model_fields) >= {
        "sequence_index",
        "score_record_id",
        "instrument_key",
        "score",
        "components",
        "scoring_policy_version_id",
        "scoring_weight_profile_id",
    }
    assert set(BriefingProvenance.model_fields) >= {
        "config_fingerprint",
        "input_fingerprint",
        "source_identifiers",
        "upstream_scoring_config_fingerprint",
        "upstream_scoring_input_fingerprint",
    }
    assert len(result.briefing_id) == 64
    assert len(result.provenance.config_fingerprint) == 64


def test_premarket_morning_briefing_surface_does_not_leak_into_strategy_sdk() -> None:
    assert tuple(bergama_strategy_sdk.__all__) == FROZEN_PUBLIC_API
    sdk_public = set(bergama_strategy_sdk.__all__)
    for symbol in premarket_all:
        assert symbol not in sdk_public


def test_premarket_exports_include_morning_briefing() -> None:
    assert "assemble_briefing" in premarket_all
    assert "BriefingCollection" in premarket_all
    assert "BRIEFING_POLICY_VERSION_V1" in premarket_all
    assert "BRIEFING_DIGEST_METHOD_V1" in premarket_all
    assert "BRIEFING_ORDERING_PRESERVATION_POLICY_V1" in premarket_all
    assert "BRIEFING_PROVENANCE_SPECIFICATION_V1" in premarket_all
    assert "BRIEFING_IDENTITY_SPECIFICATION_V1" in premarket_all
    # Unprefixed briefing constants must not collide on the Premarket surface.
    assert "DIGEST_METHOD_V1" not in premarket_all
    assert "ORDERING_PRESERVATION_POLICY_V1" not in premarket_all
    assert "PROVENANCE_SPECIFICATION_V1" not in premarket_all


def test_unauthorized_extra_request_field_fail_closed() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        BriefingRequest(
            scores=_scores(),
            as_of=AS_OF,
            config=BriefingConfig(),
            unauthorized_field="nope",  # type: ignore[call-arg]
        )


def test_briefing_models_reject_mutation() -> None:
    from pydantic import ValidationError

    result = assemble_briefing(
        BriefingRequest(scores=_scores(), as_of=AS_OF, config=BriefingConfig())
    )
    config = BriefingConfig()
    with pytest.raises(ValidationError):
        config.policy_version_id = "morning-briefing.policy.v2"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        result.briefing_id = "0" * 64  # type: ignore[misc]
    with pytest.raises(ValidationError):
        result.records[0].score = result.records[0].score  # type: ignore[misc]
