"""Optional live Polygon WebSocket smoke — SKIPPED unless explicitly enabled."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime

import pytest
from app.core.clock import SystemClock
from app.core.polygon_settings import PolygonSettings
from app.infrastructure.polygon.realtime import (
    ConnectionState,
    PolygonRealtimeConnector,
    RealtimeStartRequest,
    SymbolRealtimeContext,
)
from app.market_data.enums import AssetClass
from app.market_data.identity import InstrumentId
from pydantic import SecretStr


def _live_enabled() -> bool:
    return os.environ.get("BERGAMA_POLYGON_WS_SMOKE") == "1"


@pytest.mark.asyncio
async def test_polygon_realtime_live_smoke() -> None:
    """
    Live policy:
    - SKIPPED when BERGAMA_POLYGON_WS_SMOKE is not exactly \"1\".
    - PASS only when a real WebSocket session receives a control or market frame.
    - FAIL when explicitly enabled and the provider session fails.
    """
    if not _live_enabled():
        pytest.skip(
            "smoke-api-polygon-realtime SKIPPED "
            "(set BERGAMA_POLYGON_WS_SMOKE=1 and BERGAMA_POLYGON__API_KEY)"
        )

    raw_key = os.environ.get("BERGAMA_POLYGON__API_KEY", "").strip()
    if not raw_key:
        pytest.fail("BERGAMA_POLYGON_WS_SMOKE=1 requires BERGAMA_POLYGON__API_KEY")

    settings = PolygonSettings(
        enabled=True,
        websocket_enabled=True,
        api_key=SecretStr(raw_key),
        websocket_max_reconnect_attempts=1,
        websocket_max_queue_size=10,
        websocket_auth_timeout_seconds=15.0,
    )
    connector = PolygonRealtimeConnector(settings, clock=SystemClock())
    request = RealtimeStartRequest(
        symbols=(
            SymbolRealtimeContext(
                symbol="AAPL",
                instrument=InstrumentId(
                    instrument_key="bergama:equity:us:aapl",
                    asset_class=AssetClass.EQUITY,
                    local_symbol="AAPL",
                    symbol_effective_from=datetime(2020, 1, 1, tzinfo=UTC),
                ),
                currency="USD",
                venue="XNAS",
                channels=("T",),
            ),
        )
    )
    try:
        await connector.start(request)
        # Auth + subscribe acknowledgment should reach STREAMING without leaking secrets.
        for _ in range(50):
            if connector.state is ConnectionState.STREAMING:
                break
            if connector._fatal is not None:
                raise connector._fatal
            await asyncio.sleep(0.2)
        assert connector.state is ConnectionState.STREAMING
        # Optional: try to receive one market event with a bounded wait; status-only is OK.
        try:
            event = await connector.get_event(timeout=5.0)
            assert event.source.provider == "polygon"
        except TimeoutError:
            # Still PASS if session authenticated and subscribed (market may be quiet).
            pass
    finally:
        await connector.aclose()
