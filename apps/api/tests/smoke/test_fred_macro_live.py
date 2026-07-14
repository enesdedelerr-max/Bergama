"""Optional live FRED smoke — SKIPPED unless explicitly enabled."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest
from app.core.clock import SystemClock
from app.core.fred_settings import FredSettings
from app.infrastructure.fred.http import FredHttpClient
from app.infrastructure.fred.observations import (
    FredObservationsConnector,
    ObservationsRequest,
)
from app.infrastructure.fred.series import FredSeriesConnector, SeriesRequest
from app.market_data.enums import AssetClass
from app.market_data.identity import InstrumentId
from app.market_data.serialization import market_event_to_envelope, market_event_to_payload
from pydantic import SecretStr


def _live_enabled() -> bool:
    return os.environ.get("BERGAMA_FRED_SMOKE") == "1"


@pytest.mark.asyncio
async def test_fred_macro_live_smoke() -> None:
    """
    Live policy:
    - SKIPPED when BERGAMA_FRED_SMOKE is not exactly \"1\".
    - PASS only when real series + bounded observations calls succeed.
    - FAIL when explicitly enabled and the provider call fails.
    - Never prints the API key.
    """
    if not _live_enabled():
        pytest.skip("smoke-api-fred SKIPPED (set BERGAMA_FRED_SMOKE=1 and API key)")

    raw_key = os.environ.get("BERGAMA_FRED__API_KEY", "").strip()
    if not raw_key:
        pytest.fail("BERGAMA_FRED_SMOKE=1 requires BERGAMA_FRED__API_KEY")

    settings = FredSettings(
        enabled=True,
        api_key=SecretStr(raw_key),
        max_retries=2,
        max_pages=1,
        max_results_per_page=5,
    )
    http = FredHttpClient(settings)
    clock = SystemClock()
    series = FredSeriesConnector(http, clock=clock)
    observations = FredObservationsConnector(http, clock=clock)
    instrument = InstrumentId(
        instrument_key="bergama:macro:us:gdp",
        asset_class=AssetClass.MACRO,
        local_symbol="GDP",
        symbol_effective_from=datetime(2020, 1, 1, tzinfo=UTC),
    )
    try:
        meta = await series.fetch_series(SeriesRequest(series_id="GDP"))
        result = await observations.fetch_observations(
            ObservationsRequest(
                fred_series_id="GDP",
                series_id="US_GDP",
                instrument=instrument,
                series_meta=meta,
                observation_start="2020-01-01",
                observation_end="2020-12-31",
            )
        )
    finally:
        await http.aclose()

    assert meta.fred_series_id == "GDP"
    assert result.pages_fetched >= 1
    assert len(result.events) >= 1
    first = result.events[0]
    assert first.series_id == "US_GDP"
    assert first.source.provider == "fred"
    payload = market_event_to_payload(first)
    envelope = market_event_to_envelope(first)
    assert payload["series_id"] == "US_GDP"
    assert envelope.schema_version == first.schema_version
    assert raw_key not in str(payload)
    assert raw_key not in str(envelope.payload)
    assert all(raw_key not in ref for ref in result.endpoint_refs)
