"""Contract tests for Dashboard Foundation."""

from __future__ import annotations

from datetime import UTC, datetime

import bergama_strategy_sdk
import pytest
from app.dashboard import __all__ as dashboard_all
from app.dashboard.engine import assemble_dashboard
from app.dashboard.models import (
    DashboardConfig,
    DashboardPresentationOutput,
    DashboardPresentationRecord,
    DashboardProvenance,
    DashboardRequest,
)
from app.dashboard.policy import (
    DIGEST_METHOD_V1,
    IDENTITY_SPECIFICATION_V1,
    ORDERING_PRESERVATION_POLICY_V1,
    OUTPUT_COMPLETENESS_POLICY_V1,
    POLICY_VERSION_V1,
    PRESENTATION_SELECTION_POLICY_V1,
    PROVENANCE_SPECIFICATION_V1,
    REPLAY_EQUALITY_POLICY_V1,
)
from app.premarket.morning_briefing import assemble_briefing_from_parts
from app.premarket.scoring.engine import scan_scores
from app.premarket.scoring.models import ScoreConfig, ScoreRequest
from app.premarket.watchlist.models import Watchlist, WatchlistEntry, WatchlistProvenance
from pydantic import ValidationError
from tests.contract.test_strategy_sdk_contract import FROZEN_PUBLIC_API

AS_OF = datetime(2026, 7, 17, 14, 0, tzinfo=UTC)


def _briefing():
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
    return assemble_briefing_from_parts(scores=scores, as_of=AS_OF)


def test_dashboard_models_are_frozen_and_forbid_extra() -> None:
    for model in (
        DashboardConfig,
        DashboardRequest,
        DashboardPresentationRecord,
        DashboardProvenance,
        DashboardPresentationOutput,
    ):
        assert model.model_config.get("frozen") is True
        assert model.model_config.get("extra") == "forbid"


def test_dashboard_output_contract_fields() -> None:
    result = assemble_dashboard(
        DashboardRequest(briefing=_briefing(), as_of=AS_OF, config=DashboardConfig())
    )
    assert set(DashboardPresentationOutput.model_fields) >= {
        "dashboard_output_id",
        "policy_version_id",
        "ordering_preservation_policy_id",
        "presentation_selection_policy_id",
        "as_of",
        "records",
        "provenance",
    }
    assert set(DashboardPresentationRecord.model_fields) >= {
        "sequence_index",
        "score_record_id",
        "instrument_key",
        "local_symbol",
        "score",
        "components",
        "morning_briefing_policy_version_id",
        "scoring_policy_version_id",
        "scoring_as_of",
    }
    assert set(DashboardProvenance.model_fields) >= {
        "policy_version_id",
        "ordering_preservation_policy_id",
        "presentation_selection_policy_id",
        "identity_specification_id",
        "provenance_specification_id",
        "digest_method_id",
        "as_of",
        "config_fingerprint",
        "input_fingerprint",
        "source_identifiers",
        "upstream_briefing_id",
        "upstream_briefing_config_fingerprint",
        "upstream_briefing_input_fingerprint",
    }
    assert len(result.dashboard_output_id) == 64
    assert len(result.provenance.config_fingerprint) == 64
    assert result.policy_version_id == POLICY_VERSION_V1
    assert result.ordering_preservation_policy_id == ORDERING_PRESERVATION_POLICY_V1
    assert result.presentation_selection_policy_id == PRESENTATION_SELECTION_POLICY_V1


def test_dashboard_public_export_contract() -> None:
    required = {
        "POLICY_VERSION_V1",
        "ORDERING_PRESERVATION_POLICY_V1",
        "PRESENTATION_SELECTION_POLICY_V1",
        "IDENTITY_SPECIFICATION_V1",
        "PROVENANCE_SPECIFICATION_V1",
        "DIGEST_METHOD_V1",
        "OUTPUT_COMPLETENESS_POLICY_V1",
        "REPLAY_EQUALITY_POLICY_V1",
        "DashboardConfig",
        "DashboardRequest",
        "DashboardPresentationRecord",
        "DashboardProvenance",
        "DashboardPresentationOutput",
        "assemble_dashboard",
        "assemble_dashboard_from_parts",
        "reassemble",
        "assert_replay_equal",
    }
    assert required <= set(dashboard_all)
    assert POLICY_VERSION_V1 == "dashboard.policy.v1"
    assert ORDERING_PRESERVATION_POLICY_V1 == "preserve_morning_briefing_order.v1"
    assert PRESENTATION_SELECTION_POLICY_V1 == "include_all_morning_briefing_records.v1"
    assert IDENTITY_SPECIFICATION_V1 == "dashboard.identity.v1"
    assert PROVENANCE_SPECIFICATION_V1 == "dashboard.provenance.v1"
    assert DIGEST_METHOD_V1 == "canonical_payload_sha256_v1"
    assert OUTPUT_COMPLETENESS_POLICY_V1 == "output_completeness.exactly_one_complete_output.v1"
    assert REPLAY_EQUALITY_POLICY_V1 == "replay_equality.structural_complete.v1"


def test_dashboard_surface_does_not_expand_strategy_sdk() -> None:
    assert tuple(bergama_strategy_sdk.__all__) == FROZEN_PUBLIC_API
    sdk_public = set(bergama_strategy_sdk.__all__)
    for symbol in dashboard_all:
        assert symbol not in sdk_public


def test_unauthorized_extra_request_field_fail_closed() -> None:
    with pytest.raises(ValidationError):
        DashboardRequest(
            briefing=_briefing(),
            as_of=AS_OF,
            config=DashboardConfig(),
            unauthorized_field="nope",  # type: ignore[call-arg]
        )


def test_dashboard_models_reject_mutation() -> None:
    result = assemble_dashboard(
        DashboardRequest(briefing=_briefing(), as_of=AS_OF, config=DashboardConfig())
    )
    config = DashboardConfig()
    with pytest.raises(ValidationError):
        config.policy_version_id = "dashboard.policy.v2"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        result.dashboard_output_id = "0" * 64  # type: ignore[misc]
    with pytest.raises(ValidationError):
        result.records[0].score = result.records[0].score  # type: ignore[misc]
