"""Unit tests for canonical market-data contracts (Issue #301)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.market_data.enums import AdjustmentState, AssetClass
from app.market_data.events.quote import QuoteEvent
from app.market_data.identity import InstrumentId
from app.market_data.keys import build_deduplication_key, build_idempotency_key
from app.market_data.money import canonical_decimal_str
from app.market_data.quality import DataQualityFlags
from app.market_data.serialization import market_event_to_payload
from pydantic import ValidationError
from tests.support.market_data_fixtures import (
    T0,
    instrument,
    make_bar,
    make_filing,
    make_fundamental,
    make_macro,
    make_news,
    make_quote,
    make_reference,
    make_trade,
    source,
)


def test_valid_quote_trade_bar_and_peers() -> None:
    assert make_quote().event_type.value == "quote"
    assert make_trade().price == Decimal("190.12")
    assert make_bar().volume == Decimal("10000")
    assert make_reference().isin == "US0378331005"
    assert make_fundamental().metric_code == "eps_basic"
    assert make_macro().series_id == "GDP"
    assert make_filing().form_type == "10-K"
    assert make_news().headline.startswith("Apple")


def test_utc_timezone_enforcement() -> None:
    naive = datetime(2026, 7, 13, 14, 30, 0)
    with pytest.raises(ValueError, match="timezone-aware"):
        make_quote(occurred_at=naive)


def test_invalid_pit_ordering_rejected() -> None:
    with pytest.raises(ValueError, match="occurred_at must be <= known_at"):
        make_quote(known_at=T0 - timedelta(seconds=1))


def test_known_at_after_ingested_requires_late_flag() -> None:
    with pytest.raises(ValueError, match="is_late"):
        make_quote(
            known_at=T0 + timedelta(seconds=5),
            ingested_at=T0 + timedelta(seconds=1),
            quality=DataQualityFlags(),
        )


def test_legitimate_late_arrival_semantics() -> None:
    event = make_quote(
        known_at=T0 + timedelta(seconds=5),
        ingested_at=T0 + timedelta(seconds=1),
        quality=DataQualityFlags(is_late=True, late_arrival_lag_ms=4000),
    )
    assert event.quality.is_late is True


def test_revision_semantics() -> None:
    with pytest.raises(ValueError, match="revision"):
        make_trade(quality=DataQualityFlags(is_revision=True))
    revised = make_trade(
        quality=DataQualityFlags(is_revision=True, revision_of_event_id="prior-1"),
        source=source(source_event_id="evt-2"),
    )
    assert revised.quality.revision_of_event_id == "prior-1"
    assert "rev" in build_idempotency_key(revised)


def test_deterministic_idempotency_and_dedup_keys() -> None:
    left = make_trade()
    right = make_trade()
    assert build_idempotency_key(left) == build_idempotency_key(right)
    assert build_deduplication_key(left) == build_deduplication_key(right)
    altered = make_trade(price=Decimal("191.00"))
    # Same source_event_id ⇒ same dedup key (provider id preferred).
    assert build_deduplication_key(altered) == build_deduplication_key(left)
    no_sid = make_trade(source=source(source_event_id=None), price=Decimal("190.12"))
    other = make_trade(source=source(source_event_id=None), price=Decimal("191.00"))
    assert build_deduplication_key(no_sid) != build_deduplication_key(other)


def test_key_order_independent_payload_serialization() -> None:
    event = make_quote()
    first = market_event_to_payload(event)
    second = market_event_to_payload(event)
    assert first == second
    assert list(first.keys()) == sorted(first.keys())


def test_decimal_canonical_string_serialization() -> None:
    assert canonical_decimal_str(Decimal("190.100")) == "190.1"
    payload = market_event_to_payload(make_quote(bid_price=Decimal("190.100")))
    assert payload["bid_price"] == "190.1"
    assert isinstance(payload["bid_price"], str)


def test_nan_and_infinity_rejected() -> None:
    with pytest.raises(ValueError, match="finite"):
        make_quote(bid_price=Decimal("NaN"))
    with pytest.raises(ValueError, match="finite"):
        make_trade(price=Decimal("Infinity"))


def test_source_provider_identity_retention() -> None:
    event = make_quote(
        source=source(
            provider="finnhub",
            source_symbol="AAPL.US",
            source_instrument_id="FH-1",
            extras={"channel": "trades"},
        )
    )
    assert event.source.provider == "finnhub"
    assert event.source.source_symbol == "AAPL.US"
    assert event.instrument.instrument_key == "bergama:equity:us:aapl"
    assert event.instrument.instrument_key != event.source.source_symbol


def test_effective_dated_symbol_change_compatibility() -> None:
    before = instrument(
        local_symbol="FB",
        symbol_effective_from=datetime(2012, 1, 1, tzinfo=UTC),
        symbol_effective_to=datetime(2021, 10, 27, 23, 59, 59, tzinfo=UTC),
    )
    after = instrument(
        local_symbol="META",
        symbol_effective_from=datetime(2021, 10, 28, tzinfo=UTC),
        symbol_effective_to=None,
    )
    assert before.instrument_key == after.instrument_key
    assert before.is_effective_at(datetime(2020, 6, 1, tzinfo=UTC))
    assert not before.is_effective_at(datetime(2022, 1, 1, tzinfo=UTC))
    assert after.is_effective_at(datetime(2022, 1, 1, tzinfo=UTC))


def test_currency_and_venue_validation() -> None:
    with pytest.raises(ValueError, match="currency"):
        make_quote(currency="US")
    with pytest.raises(ValueError, match="currency is required"):
        make_trade(currency=None)


def test_field_specific_zero_negative_rules() -> None:
    with pytest.raises(ValueError, match="bid_price must be > 0"):
        make_quote(bid_price=Decimal("0"))
    with pytest.raises(ValueError, match="bid_size must be >= 0"):
        make_quote(bid_size=Decimal("-1"))
    with pytest.raises(ValueError, match="size must be > 0"):
        make_trade(size=Decimal("0"))
    # Fundamentals allow zero/negative.
    assert make_fundamental(value=Decimal("0")).value == Decimal("0")
    assert make_fundamental(value=Decimal("-2.5"), unit="currency").value == Decimal("-2.5")


def test_corporate_action_adjustment_flags() -> None:
    bar = make_bar(adjustment_state=AdjustmentState.SPLIT_ADJUSTED)
    assert bar.adjustment_state is AdjustmentState.SPLIT_ADJUSTED
    payload = market_event_to_payload(bar)
    assert payload["adjustment_state"] == "split_adjusted"


def test_provider_metadata_isolation() -> None:
    event = make_news(metadata={"provider_category": "benzinga-wire"})
    assert "provider_category" in event.metadata
    leaked = make_quote().model_dump(mode="python")
    leaked["polygon_ticker"] = "AAPL"
    with pytest.raises(ValidationError):
        QuoteEvent.model_validate(leaked)


def test_forbidden_secret_metadata() -> None:
    with pytest.raises(ValueError, match="forbidden"):
        make_quote(metadata={"api_key": "secret"})


def test_instrument_key_not_provider_symbol() -> None:
    inst = InstrumentId.model_validate(
        {
            "instrument_key": "bergama:equity:us:aapl",
            "asset_class": AssetClass.EQUITY,
            "local_symbol": "AAPL",
            "symbol_effective_from": datetime(2020, 1, 1, tzinfo=UTC),
        }
    )
    assert inst.instrument_key.startswith("bergama:")
