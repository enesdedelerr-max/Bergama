"""Unit tests for Premarket Catalyst Foundation (#74)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.core.config import AppSettings
from app.core.premarket_settings import PremarketSettings
from app.market_data.events.bar import BarEvent
from app.premarket.catalyst.engine import normalize_catalysts, normalize_catalysts_from_parts
from app.premarket.catalyst.identity import build_catalyst_record_id
from app.premarket.catalyst.models import (
    CatalystClassificationRule,
    CatalystConfig,
    CatalystNormalizationRequest,
)
from app.premarket.catalyst.ordering import (
    ORDERING_POLICY_KNOWN_AT_ASC_EVENT_TIME_ASC_TYPE_ASC_INSTRUMENT_KEY_ASC_ID_ASC,
)
from app.premarket.errors import (
    CatalystClassificationError,
    CatalystIdentityConflictError,
    CatalystStaleKnownAtError,
    CatalystUnsupportedEventError,
    PremarketDisabledError,
)
from pydantic import ValidationError
from tests.support.market_data_fixtures import instrument, make_bar, make_news, source

AS_OF = datetime(2026, 7, 17, 12, 0, 0, tzinfo=UTC)
T0 = datetime(2026, 7, 17, 11, 0, 0, tzinfo=UTC)


def _rule(
    *,
    rule_id: str = "earnings-topic",
    rule_priority: int = 10,
    catalyst_type: str = "earnings",
    topics: tuple[str, ...] = ("earnings",),
) -> CatalystClassificationRule:
    return CatalystClassificationRule(
        rule_id=rule_id,
        rule_priority=rule_priority,
        catalyst_type=catalyst_type,
        match_topics=topics,
    )


def _config(
    *,
    rules: tuple[CatalystClassificationRule, ...] | None = None,
) -> CatalystConfig:
    return CatalystConfig(classification_rules=rules or (_rule(),))


def _news(**overrides: object):
    defaults = {
        "headline": "Apple earnings preview",
        "summary": "Quarterly results expected",
        "url_ref": "https://example.invalid/news/aapl-1",
        "topics": ("earnings", "tech"),
        "occurred_at": T0,
        "effective_at": T0,
        "known_at": T0 + timedelta(minutes=1),
        "ingested_at": T0 + timedelta(minutes=2),
        "source": source(provider="fixture", source_event_id="news-1"),
        "instrument": instrument(instrument_key="bergama:equity:us:aapl", local_symbol="AAPL"),
    }
    defaults.update(overrides)
    return make_news(**defaults)


def _request(events: tuple, *, config: CatalystConfig | None = None, as_of: datetime = AS_OF):
    return CatalystNormalizationRequest(
        events=events,
        as_of=as_of,
        config=config or _config(),
    )


def test_premarket_settings_disabled_by_default() -> None:
    settings = PremarketSettings()
    assert settings.enabled is False
    app = AppSettings(environment="test", bootstrap_auth_enabled=False)
    assert app.premarket.enabled is False


def test_normalize_fails_closed_when_settings_disabled() -> None:
    with pytest.raises(PremarketDisabledError) as exc_info:
        normalize_catalysts(_request((_news(),)), settings=PremarketSettings(enabled=False))
    assert exc_info.value.detail == "premarket_disabled"


def test_normalize_runs_when_enabled() -> None:
    result = normalize_catalysts(
        _request((_news(),)),
        settings=PremarketSettings(enabled=True),
    )
    assert len(result.records) == 1


def test_single_valid_event() -> None:
    event = _news()
    result = normalize_catalysts(_request((event,)))
    assert len(result.records) == 1
    record = result.records[0]
    assert record.instrument_key == "bergama:equity:us:aapl"
    assert record.local_symbol == "AAPL"
    assert record.catalyst_type == "earnings"
    assert record.event_time == T0
    assert record.known_at == T0 + timedelta(minutes=1)
    assert record.as_of == AS_OF
    assert record.source_provider == "fixture"
    assert record.source_event_id == "news-1"
    assert record.rule_id == "earnings-topic"
    assert record.catalyst_record_id == build_catalyst_record_id(event)
    assert record.source_content_fingerprint == record.catalyst_record_id
    assert (
        result.provenance.ordering_policy_id
        == ORDERING_POLICY_KNOWN_AT_ASC_EVENT_TIME_ASC_TYPE_ASC_INSTRUMENT_KEY_ASC_ID_ASC
    )


def test_multiple_events_deterministic_ordering() -> None:
    earlier = _news(
        headline="Earlier",
        source=source(provider="fixture", source_event_id="n-early"),
        occurred_at=T0,
        effective_at=T0,
        known_at=T0 + timedelta(minutes=1),
        ingested_at=T0 + timedelta(minutes=2),
        topics=("earnings",),
        instrument=instrument(instrument_key="bergama:equity:us:msft", local_symbol="MSFT"),
    )
    later = _news(
        headline="Later",
        source=source(provider="fixture", source_event_id="n-late"),
        occurred_at=T0 + timedelta(minutes=5),
        effective_at=T0 + timedelta(minutes=5),
        known_at=T0 + timedelta(minutes=10),
        ingested_at=T0 + timedelta(minutes=11),
        topics=("earnings",),
        instrument=instrument(instrument_key="bergama:equity:us:aapl", local_symbol="AAPL"),
    )
    product = _news(
        headline="Product",
        source=source(provider="fixture", source_event_id="n-product"),
        occurred_at=T0 + timedelta(minutes=1),
        effective_at=T0 + timedelta(minutes=1),
        known_at=T0 + timedelta(minutes=1),
        ingested_at=T0 + timedelta(minutes=2),
        topics=("product",),
        instrument=instrument(instrument_key="bergama:equity:us:aapl", local_symbol="AAPL"),
    )
    config = _config(
        rules=(
            _rule(
                rule_id="earnings",
                rule_priority=10,
                catalyst_type="earnings",
                topics=("earnings",),
            ),
            _rule(
                rule_id="product",
                rule_priority=20,
                catalyst_type="product",
                topics=("product",),
            ),
        )
    )
    result = normalize_catalysts(_request((later, product, earlier), config=config))
    assert [r.source_event_id for r in result.records] == ["n-early", "n-product", "n-late"]
    assert [r.catalyst_type for r in result.records] == ["earnings", "product", "earnings"]


def test_deterministic_identity_and_replay_equality() -> None:
    event = _news()
    first = normalize_catalysts(_request((event,)))
    second = normalize_catalysts(_request((event,)))
    assert first.model_dump() == second.model_dump()
    assert first.provenance.input_fingerprint == second.provenance.input_fingerprint
    assert first.records[0].catalyst_record_id == build_catalyst_record_id(event)


def test_exact_semantic_duplicates_collapse() -> None:
    event = _news()
    result = normalize_catalysts(_request((event, event)))
    assert len(result.records) == 1
    assert result.provenance.source_identifiers == (result.records[0].catalyst_record_id,)


def test_source_identity_conflict_fails_closed() -> None:
    base = _news(source=source(provider="fixture", source_event_id="same-id"))
    conflict = _news(
        headline="Different headline same source id",
        source=source(provider="fixture", source_event_id="same-id"),
    )
    assert build_catalyst_record_id(base) != build_catalyst_record_id(conflict)
    with pytest.raises(CatalystIdentityConflictError) as exc_info:
        normalize_catalysts(_request((base, conflict)))
    assert "source_identity_conflict" in (exc_info.value.detail or "")


def test_missing_provider_id_uses_content_derived_identity() -> None:
    event = _news(source=source(provider="fixture", source_event_id=None))
    result = normalize_catalysts(_request((event,)))
    assert result.records[0].source_event_id is None
    assert result.records[0].catalyst_record_id == build_catalyst_record_id(event)
    collapsed = normalize_catalysts(_request((event, event)))
    assert len(collapsed.records) == 1


def test_linked_instrument_uses_instrument_key() -> None:
    event = _news(
        instrument=instrument(
            instrument_key="bergama:equity:us:aapl",
            local_symbol="AAPL",
        )
    )
    result = normalize_catalysts(_request((event,)))
    assert result.records[0].instrument_key == "bergama:equity:us:aapl"
    assert result.records[0].local_symbol == "AAPL"


def test_unlinked_style_instrument_ordering_is_deterministic() -> None:
    """NewsEvent always carries InstrumentId; market-wide keys still sort stably."""
    unlinked = _news(
        headline="Market wide",
        source=source(provider="fixture", source_event_id="unlinked-1"),
        instrument=instrument(
            instrument_key="bergama:news:market:unlinked",
            local_symbol="MARKET",
        ),
        topics=("earnings",),
        occurred_at=T0,
        effective_at=T0,
        known_at=T0 + timedelta(minutes=1),
        ingested_at=T0 + timedelta(minutes=2),
    )
    linked = _news(
        headline="AAPL linked",
        source=source(provider="fixture", source_event_id="linked-1"),
        instrument=instrument(instrument_key="bergama:equity:us:aapl", local_symbol="AAPL"),
        topics=("earnings",),
        occurred_at=T0,
        effective_at=T0,
        known_at=T0 + timedelta(minutes=1),
        ingested_at=T0 + timedelta(minutes=2),
    )
    result = normalize_catalysts(_request((unlinked, linked)))
    keys = [record.instrument_key for record in result.records]
    assert keys == sorted(keys)


def test_naive_as_of_rejected() -> None:
    with pytest.raises(ValidationError):
        CatalystNormalizationRequest(
            events=(_news(),),
            as_of=datetime(2026, 7, 17, 12, 0, 0),
            config=_config(),
        )


def test_event_time_versus_known_at_preserved() -> None:
    event = _news(
        occurred_at=T0,
        effective_at=T0,
        known_at=T0 + timedelta(minutes=30),
        ingested_at=T0 + timedelta(minutes=31),
    )
    record = normalize_catalysts(_request((event,))).records[0]
    assert record.event_time == T0
    assert record.known_at == T0 + timedelta(minutes=30)
    assert record.event_time != record.known_at


def test_known_at_after_as_of_fails_closed() -> None:
    event = _news(
        known_at=AS_OF + timedelta(seconds=1),
        ingested_at=AS_OF + timedelta(seconds=2),
    )
    with pytest.raises(CatalystStaleKnownAtError):
        normalize_catalysts(_request((event,)))


def test_empty_input_returns_empty_collection_with_provenance() -> None:
    result = normalize_catalysts(_request(()))
    assert result.records == ()
    assert len(result.provenance.config_fingerprint) == 64
    assert len(result.provenance.input_fingerprint) == 64
    assert result.provenance.source_identifiers == ()


def test_unsupported_event_type_fails_closed() -> None:
    bar: BarEvent = make_bar()
    with pytest.raises(CatalystUnsupportedEventError):
        normalize_catalysts_from_parts(events=(bar,), as_of=AS_OF, config=_config())


def test_invalid_classification_mapping_fails_closed() -> None:
    event = _news(topics=("unmapped-topic",))
    with pytest.raises(CatalystClassificationError):
        normalize_catalysts(_request((event,)))


def test_fingerprint_changes_when_input_or_config_changes() -> None:
    base = normalize_catalysts(_request((_news(),)))
    changed_event = normalize_catalysts(
        _request((_news(headline="Changed headline", source=source(source_event_id="news-2")),))
    )
    changed_config = normalize_catalysts(
        _request(
            (_news(),),
            config=_config(
                rules=(_rule(rule_id="alt", catalyst_type="earnings", topics=("earnings", "tech")),)
            ),
        )
    )
    assert base.provenance.input_fingerprint != changed_event.provenance.input_fingerprint
    assert base.provenance.config_fingerprint != changed_config.provenance.config_fingerprint


def test_from_parts_accepts_news_events() -> None:
    result = normalize_catalysts_from_parts(
        events=(_news(),),
        as_of=AS_OF,
        config=_config(),
    )
    assert len(result.records) == 1
