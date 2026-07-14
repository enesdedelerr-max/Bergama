"""Optional live Finnhub smoke — SKIPPED unless explicitly enabled."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest
from app.core.clock import SystemClock
from app.core.finnhub_settings import FinnhubSettings
from app.infrastructure.finnhub.fundamentals import (
    FinnhubFundamentalsConnector,
    FundamentalsRequest,
)
from app.infrastructure.finnhub.http import FinnhubHttpClient
from app.infrastructure.finnhub.reference import FinnhubReferenceConnector, ReferenceRequest
from app.market_data.enums import AssetClass
from app.market_data.identity import InstrumentId
from app.market_data.serialization import market_event_to_envelope, market_event_to_payload
from pydantic import SecretStr


def _live_enabled() -> bool:
    return os.environ.get("BERGAMA_FINNHUB_SMOKE") == "1"


@pytest.mark.asyncio
async def test_finnhub_fundamentals_live_smoke() -> None:
    """
    Live policy:
    - SKIPPED when BERGAMA_FINNHUB_SMOKE is not exactly \"1\".
    - PASS only when real profile + metric calls succeed and map canonically.
    - FAIL when explicitly enabled and the provider call fails.
    - Never prints the API key.
    """
    if not _live_enabled():
        pytest.skip("smoke-api-finnhub SKIPPED (set BERGAMA_FINNHUB_SMOKE=1 and API key)")

    raw_key = os.environ.get("BERGAMA_FINNHUB__API_KEY", "").strip()
    if not raw_key:
        pytest.fail("BERGAMA_FINNHUB_SMOKE=1 requires BERGAMA_FINNHUB__API_KEY")

    settings = FinnhubSettings(
        enabled=True,
        api_key=SecretStr(raw_key),
        max_retries=2,
    )
    http = FinnhubHttpClient(settings)
    clock = SystemClock()
    reference = FinnhubReferenceConnector(http, clock=clock)
    fundamentals = FinnhubFundamentalsConnector(http, clock=clock)
    instrument = InstrumentId(
        instrument_key="bergama:equity:us:aapl",
        asset_class=AssetClass.EQUITY,
        local_symbol="AAPL",
        symbol_effective_from=datetime(2020, 1, 1, tzinfo=UTC),
    )
    try:
        profile_event = await reference.fetch_reference(
            ReferenceRequest(symbol="AAPL", instrument=instrument, currency="USD")
        )
        metric_result = await fundamentals.fetch_fundamentals(
            FundamentalsRequest(symbol="AAPL", instrument=instrument, currency="USD")
        )
    finally:
        await http.aclose()

    assert profile_event.source.provider == "finnhub"
    assert profile_event.isin is None
    assert profile_event.exchange_mic is None
    envelope = market_event_to_envelope(profile_event)
    assert envelope.schema_version == profile_event.schema_version
    assert envelope.payload.get("event_type") == profile_event.event_type.value

    assert metric_result.metric_count == len(metric_result.events)
    assert metric_result.metric_count >= 1
    first = metric_result.events[0]
    payload = market_event_to_payload(first)
    assert payload["metric_code"] == first.metric_code
    assert raw_key not in str(payload)
    assert raw_key not in str(envelope.payload)
