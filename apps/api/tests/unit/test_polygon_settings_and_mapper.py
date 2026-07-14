"""Unit tests for Polygon settings and mapping helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.core.clock import FixedClock
from app.core.polygon_settings import PolygonSettings
from app.infrastructure.polygon.errors import PolygonInvalidRequestError, PolygonMappingFailedError
from app.infrastructure.polygon.historical import HistoricalBarsRequest, PolygonTimespan
from app.infrastructure.polygon.mapper import (
    DAILY_WINDOW_POLICY,
    decimal_from_provider,
    map_bar_event,
    ms_to_utc,
    timespan_duration,
)
from app.infrastructure.polygon.pagination import sanitize_url, validate_next_url
from app.infrastructure.polygon.schemas import PolygonAggBar, PolygonAggsResponse
from app.market_data.enums import AdjustmentState, AssetClass
from app.market_data.identity import InstrumentId
from app.market_data.keys import build_deduplication_key, build_idempotency_key
from app.market_data.serialization import market_event_to_envelope, market_event_to_payload
from pydantic import SecretStr


def _instrument() -> InstrumentId:
    return InstrumentId(
        instrument_key="bergama:equity:us:aapl",
        asset_class=AssetClass.EQUITY,
        local_symbol="AAPL",
        symbol_effective_from=datetime(2020, 1, 1, tzinfo=UTC),
    )


def test_settings_disabled_by_default() -> None:
    settings = PolygonSettings()
    assert settings.enabled is False
    assert settings.api_key is None


def test_api_key_required_only_when_enabled() -> None:
    PolygonSettings(enabled=False)
    with pytest.raises(ValueError, match="API_KEY"):
        PolygonSettings(enabled=True)
    configured = PolygonSettings(
        enabled=True,
        api_key=SecretStr("test-polygon-key-value"),
    )
    assert configured.api_key is not None
    summary = configured.safe_summary()
    assert summary["api_key_configured"] is True
    assert "test-polygon" not in str(summary)


def test_secretstr_redaction_in_repr() -> None:
    settings = PolygonSettings(enabled=True, api_key=SecretStr("super-secret-key-abc"))
    text = repr(settings)
    assert "super-secret-key-abc" not in text


def test_request_validation() -> None:
    start = datetime(2024, 1, 1, tzinfo=UTC)
    end = datetime(2024, 1, 2, tzinfo=UTC)
    HistoricalBarsRequest(
        symbol="aapl",
        instrument=_instrument(),
        currency="usd",
        timespan=PolygonTimespan.MINUTE,
        start=start,
        end=end,
        multiplier=5,
        limit=100,
    )
    with pytest.raises(ValueError):
        HistoricalBarsRequest(
            symbol="AAPL",
            instrument=_instrument(),
            currency="USD",
            timespan=PolygonTimespan.DAY,
            start=end,
            end=start,
        )
    with pytest.raises(ValueError):
        HistoricalBarsRequest(
            symbol="AAPL",
            instrument=_instrument(),
            currency="US",
            timespan=PolygonTimespan.DAY,
            start=start,
            end=end,
        )


def test_minute_hour_day_window_derivation_and_dst() -> None:
    # DST spring forward US/Eastern 2024-03-10; provider t is UTC ms.
    start = datetime(2024, 3, 10, 6, 0, tzinfo=UTC)
    assert timespan_duration(timespan="minute", multiplier=5) == timedelta(minutes=5)
    assert timespan_duration(timespan="hour", multiplier=1) == timedelta(hours=1)
    day = timespan_duration(timespan="day", multiplier=1)
    assert day == timedelta(days=1)
    # Exact duration arithmetic across DST for hour bars (no wall-clock invent).
    end = start + timespan_duration(timespan="hour", multiplier=2)
    assert end - start == timedelta(hours=2)


def test_ms_to_utc_and_decimal() -> None:
    assert ms_to_utc(1_577_941_200_000) == datetime(2020, 1, 2, 5, 0, tzinfo=UTC)
    assert decimal_from_provider("75.0875", field_name="open") == Decimal("75.0875")
    with pytest.raises(ValueError):
        decimal_from_provider("NaN", field_name="open")
    with pytest.raises(ValueError):
        decimal_from_provider("Infinity", field_name="open")


def test_sanitize_and_cross_host_next_url() -> None:
    dirty = "https://api.polygon.io/v2/aggs?apiKey=SECRET&cursor=1"
    assert "SECRET" not in sanitize_url(dirty)
    assert "apiKey" not in sanitize_url(dirty)
    validate_next_url(
        next_url="https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/1/2?cursor=1",
        base_url="https://api.polygon.io",
    )
    with pytest.raises(PolygonInvalidRequestError):
        validate_next_url(
            next_url="https://evil.example/v2/aggs",
            base_url="https://api.polygon.io",
        )
    with pytest.raises(PolygonInvalidRequestError):
        validate_next_url(
            next_url="http://api.polygon.io/v2/aggs",
            base_url="https://api.polygon.io",
        )


def test_map_bar_preserves_identity_currency_and_keys() -> None:
    clock = FixedClock(datetime(2024, 1, 2, 12, 0, tzinfo=UTC))
    response = PolygonAggsResponse(
        status="OK",
        request_id="req-1",
        ticker="AAPL",
        adjusted=True,
        results=[
            PolygonAggBar.model_validate(
                {
                    "o": 10,
                    "h": 12,
                    "l": 9,
                    "c": 11,
                    "v": 1000,
                    "vw": 10.5,
                    "t": 1_704_110_400_000,
                    "n": 3,
                }
            )
        ],
    )
    event = map_bar_event(
        response.results[0],
        response=response,
        instrument=_instrument(),
        currency="USD",
        venue="XNAS",
        timespan="day",
        multiplier=1,
        requested_adjusted=True,
        known_at=clock.now(),
        clock=clock,
        endpoint_ref="https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/a/b",
        bar_index=0,
        request_symbol="AAPL",
    )
    assert event.instrument.instrument_key == "bergama:equity:us:aapl"
    assert event.currency == "USD"
    assert event.source.provider == "polygon"
    assert event.source.source_symbol == "AAPL"
    assert event.source.source_event_id == "req-1:1704110400000:0"
    assert event.adjustment_state is AdjustmentState.SPLIT_ADJUSTED
    assert event.source.extras.get("window_policy") == DAILY_WINDOW_POLICY
    assert "polygon_ticker" not in event.model_dump()
    assert build_idempotency_key(event)
    assert build_deduplication_key(event)
    payload = market_event_to_payload(event)
    assert payload["open"] == "10"
    env = market_event_to_envelope(event)
    assert env.occurred_at == event.occurred_at


def test_negative_volume_and_ohlc_rejected() -> None:
    clock = FixedClock(datetime(2024, 1, 2, 12, 0, tzinfo=UTC))
    response = PolygonAggsResponse(status="OK", request_id="r", ticker="AAPL", adjusted=False)
    bad_vol = PolygonAggBar.model_validate(
        {"o": 1, "h": 1, "l": 1, "c": 1, "v": -1, "t": 1_700_000_000_000}
    )
    with pytest.raises((PolygonMappingFailedError, ValueError)):
        map_bar_event(
            bad_vol,
            response=response,
            instrument=_instrument(),
            currency="USD",
            venue=None,
            timespan="minute",
            multiplier=1,
            requested_adjusted=False,
            known_at=clock.now(),
            clock=clock,
            endpoint_ref="https://api.polygon.io/x",
            bar_index=0,
            request_symbol="AAPL",
        )
