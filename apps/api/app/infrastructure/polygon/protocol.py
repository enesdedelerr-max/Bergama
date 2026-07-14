"""Provider-independent historical bar connector protocol."""

from __future__ import annotations

from typing import Protocol

from app.infrastructure.polygon.historical import HistoricalBarsRequest, HistoricalBarsResult


class HistoricalBarConnector(Protocol):
    """Narrow protocol for historical OHLCV retrieval adapters."""

    async def fetch_bars(self, request: HistoricalBarsRequest) -> HistoricalBarsResult:
        """Fetch and map historical bars for the request."""
        ...
