"""Contract tests for Premarket Catalyst Foundation (#74)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import bergama_strategy_sdk
from app.market_data.events.bar import BarEvent
from app.market_data.events.news import NewsEvent
from app.market_data.identity import InstrumentId
from app.premarket import __all__ as premarket_all
from app.premarket.catalyst.engine import normalize_catalysts
from app.premarket.catalyst.models import (
    CatalystClassificationRule,
    CatalystCollection,
    CatalystConfig,
    CatalystNormalizationRequest,
    CatalystProvenance,
    CatalystRecord,
)
from app.premarket.catalyst.ordering import (
    ORDERING_POLICY_KNOWN_AT_ASC_EVENT_TIME_ASC_TYPE_ASC_INSTRUMENT_KEY_ASC_ID_ASC,
)
from tests.contract.test_strategy_sdk_contract import FROZEN_PUBLIC_API
from tests.support.market_data_fixtures import make_news, source

AS_OF = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
T0 = datetime(2026, 7, 17, 11, 0, tzinfo=UTC)


def test_catalyst_models_are_frozen_and_forbid_extra() -> None:
    for model in (
        CatalystClassificationRule,
        CatalystConfig,
        CatalystNormalizationRequest,
        CatalystRecord,
        CatalystProvenance,
        CatalystCollection,
    ):
        assert model.model_config.get("frozen") is True
        assert model.model_config.get("extra") == "forbid"


def test_catalyst_output_contract_fields() -> None:
    event = make_news(
        topics=("earnings",),
        occurred_at=T0,
        effective_at=T0,
        known_at=T0 + timedelta(minutes=1),
        ingested_at=T0 + timedelta(minutes=2),
        source=source(provider="fixture", source_event_id="c-1"),
    )
    result = normalize_catalysts(
        CatalystNormalizationRequest(
            events=(event,),
            as_of=AS_OF,
            config=CatalystConfig(
                classification_rules=(
                    CatalystClassificationRule(
                        rule_id="earnings",
                        rule_priority=1,
                        catalyst_type="earnings",
                        match_topics=("earnings",),
                    ),
                )
            ),
        )
    )
    assert set(CatalystRecord.model_fields) >= {
        "catalyst_record_id",
        "source_event_id",
        "source_content_fingerprint",
        "instrument_key",
        "local_symbol",
        "catalyst_type",
        "event_time",
        "known_at",
        "as_of",
        "source_provider",
        "rule_id",
    }
    assert set(CatalystProvenance.model_fields) >= {
        "config_fingerprint",
        "input_fingerprint",
        "ordering_policy_id",
        "source_identifiers",
    }
    assert (
        result.provenance.ordering_policy_id
        == ORDERING_POLICY_KNOWN_AT_ASC_EVENT_TIME_ASC_TYPE_ASC_INSTRUMENT_KEY_ASC_ID_ASC
    )
    assert len(result.provenance.config_fingerprint) == 64
    assert len(result.provenance.input_fingerprint) == 64


def test_premarket_catalyst_surface_does_not_leak_into_strategy_sdk() -> None:
    assert tuple(bergama_strategy_sdk.__all__) == FROZEN_PUBLIC_API
    sdk_public = set(bergama_strategy_sdk.__all__)
    for symbol in premarket_all:
        assert symbol not in sdk_public


def test_market_data_news_and_bar_contracts_unchanged_by_catalyst_import() -> None:
    news_fields = set(NewsEvent.model_fields)
    assert "headline" in news_fields
    assert "topics" in news_fields
    assert "instrument" in news_fields
    bar_fields = set(BarEvent.model_fields)
    assert "close_time" in bar_fields
    assert InstrumentId.model_fields["instrument_key"] is not None
