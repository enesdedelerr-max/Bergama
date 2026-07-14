"""Cross-provider Decimal / value contracts (#304E)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.infrastructure.finnhub.errors import FinnhubMappingFailedError
from app.infrastructure.finnhub.mapper import map_fundamental_events
from app.infrastructure.finnhub.schemas import FinnhubBasicFinancials
from app.infrastructure.polygon.errors import PolygonMappingFailedError
from app.infrastructure.polygon.mapper import map_bar_event
from app.infrastructure.polygon.schemas import PolygonAggBar, PolygonAggsResponse
from app.market_data.money import require_finite_decimal
from tests.support.provider_contracts import finnhub, fred, polygon
from tests.support.provider_contracts.assertions import assert_decimal_fields_finite
from tests.support.provider_contracts.clocks import OBSERVED_AT, observed_clock
from tests.support.provider_contracts.identities import equity_instrument


def test_require_finite_decimal_rejects_nan_and_infinity() -> None:
    with pytest.raises(ValueError, match="finite"):
        require_finite_decimal("NaN", field_name="price")
    with pytest.raises(ValueError, match="finite"):
        require_finite_decimal("Infinity", field_name="price")


def test_decimal_fields_survive_transport_boundary() -> None:
    assert_decimal_fields_finite(
        polygon.historical_bar(),
        ("open", "high", "low", "close", "volume", "vwap"),
    )
    assert_decimal_fields_finite(polygon.realtime_trade(), ("price", "size"))
    assert_decimal_fields_finite(
        polygon.realtime_quote(),
        ("bid_price", "ask_price", "bid_size", "ask_size"),
    )
    assert_decimal_fields_finite(finnhub.fundamental_events()[0], ("value",))
    assert_decimal_fields_finite(fred.macro_observation(), ("value",))


def test_polygon_nan_bar_fails_closed() -> None:
    bar = PolygonAggBar.model_validate(
        {"o": "NaN", "h": "1", "l": "1", "c": "1", "v": "1", "t": 1_704_067_200_000}
    )
    response = PolygonAggsResponse.model_validate(
        {"ticker": "AAPL", "request_id": "r", "results": []}
    )
    with pytest.raises((PolygonMappingFailedError, ValueError)):
        map_bar_event(
            bar,
            response=response,
            instrument=equity_instrument(),
            currency="USD",
            venue="XNAS",
            timespan="day",
            multiplier=1,
            requested_adjusted=True,
            known_at=OBSERVED_AT,
            clock=observed_clock(),
            endpoint_ref="https://api.polygon.io/v2/aggs",
            bar_index=0,
            request_symbol="AAPL",
        )


def test_finnhub_invalid_metric_fails_closed() -> None:
    payload = FinnhubBasicFinancials.model_validate({"symbol": "AAPL", "metric": {"peTTM": "NaN"}})
    with pytest.raises(FinnhubMappingFailedError):
        map_fundamental_events(
            payload,
            instrument=equity_instrument(),
            symbol="AAPL",
            observed_at=OBSERVED_AT,
            request_id=None,
        )


def test_fred_missing_never_coerced_to_zero() -> None:
    assert fred.missing_observation() is None
    present = fred.macro_observation(value="0")
    assert present.value == Decimal("0")
