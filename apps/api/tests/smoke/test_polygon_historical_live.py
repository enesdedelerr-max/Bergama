"""Optional live Polygon smoke — SKIPPED unless explicitly enabled."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest
from app.core.clock import SystemClock
from app.core.polygon_settings import PolygonSettings
from app.infrastructure.polygon.historical import (
    HistoricalBarsRequest,
    PolygonHistoricalConnector,
    PolygonTimespan,
)
from app.infrastructure.polygon.http import PolygonHttpClient
from app.market_data.enums import AssetClass
from app.market_data.identity import InstrumentId
from pydantic import SecretStr


def _live_enabled() -> bool:
    return os.environ.get("BERGAMA_POLYGON_SMOKE") == "1"


@pytest.mark.asyncio
async def test_polygon_historical_live_smoke() -> None:
    """
    Live policy:
    - SKIPPED when BERGAMA_POLYGON_SMOKE is not exactly \"1\".
    - PASS only when a real aggregates call succeeds.
    - FAIL when explicitly enabled and the provider call fails.
    """
    if not _live_enabled():
        pytest.skip("smoke-api-polygon SKIPPED (set BERGAMA_POLYGON_SMOKE=1 and API key)")

    raw_key = os.environ.get("BERGAMA_POLYGON__API_KEY", "").strip()
    if not raw_key:
        pytest.fail("BERGAMA_POLYGON_SMOKE=1 requires BERGAMA_POLYGON__API_KEY")

    settings = PolygonSettings(
        enabled=True,
        api_key=SecretStr(raw_key),
        max_retries=2,
        max_pages=1,
        max_results_per_page=5,
    )
    http = PolygonHttpClient(settings)
    connector = PolygonHistoricalConnector(http, clock=SystemClock())
    end = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=3)
    request = HistoricalBarsRequest(
        symbol="AAPL",
        instrument=InstrumentId(
            instrument_key="bergama:equity:us:aapl",
            asset_class=AssetClass.EQUITY,
            local_symbol="AAPL",
            symbol_effective_from=datetime(2020, 1, 1, tzinfo=UTC),
        ),
        currency="USD",
        venue="XNAS",
        timespan=PolygonTimespan.DAY,
        multiplier=1,
        start=start,
        end=end,
        limit=5,
        adjusted=True,
    )
    try:
        result = await connector.fetch_bars(request)
    finally:
        await http.aclose()

    assert result.pages_fetched >= 1
    assert isinstance(result.bars, tuple)
