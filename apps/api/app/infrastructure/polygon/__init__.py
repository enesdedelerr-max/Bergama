"""Polygon REST + realtime infrastructure (Issues #302 / #303).

Transport-only connectors: no Kafka publish, Iceberg write, or persistence.

Health checks intentionally omitted for both historical and realtime providers —
configuration validation stays settings-side and must not be labeled provider health.
Realtime connection state is available on ``PolygonRealtimeConnector.state`` for
operations/tests; it is not a readiness probe.
"""

from __future__ import annotations

from app.infrastructure.polygon.errors import (
    PolygonAuthenticationFailedError,
    PolygonConnectionFailedError,
    PolygonError,
    PolygonForbiddenError,
    PolygonInvalidRequestError,
    PolygonInvalidResponseError,
    PolygonMappingFailedError,
    PolygonNotConfiguredError,
    PolygonNotFoundError,
    PolygonPaginationLimitError,
    PolygonPaginationLoopError,
    PolygonProviderError,
    PolygonRateLimitedError,
    PolygonTimeoutError,
    PolygonWebsocketAuthFailedError,
    PolygonWebsocketError,
    PolygonWebsocketOverflowError,
    PolygonWebsocketProtocolError,
    PolygonWebsocketReconnectExhaustedError,
)
from app.infrastructure.polygon.historical import (
    HistoricalBarsRequest,
    HistoricalBarsResult,
    PolygonHistoricalConnector,
    PolygonTimespan,
)
from app.infrastructure.polygon.http import PolygonHttpClient
from app.infrastructure.polygon.protocol import HistoricalBarConnector
from app.infrastructure.polygon.realtime import (
    ConnectionState,
    PolygonRealtimeConnector,
    RealtimeStartRequest,
    SymbolRealtimeContext,
)

__all__ = [
    "ConnectionState",
    "HistoricalBarConnector",
    "HistoricalBarsRequest",
    "HistoricalBarsResult",
    "PolygonAuthenticationFailedError",
    "PolygonConnectionFailedError",
    "PolygonError",
    "PolygonForbiddenError",
    "PolygonHistoricalConnector",
    "PolygonHttpClient",
    "PolygonInvalidRequestError",
    "PolygonInvalidResponseError",
    "PolygonMappingFailedError",
    "PolygonNotConfiguredError",
    "PolygonNotFoundError",
    "PolygonPaginationLimitError",
    "PolygonPaginationLoopError",
    "PolygonProviderError",
    "PolygonRateLimitedError",
    "PolygonRealtimeConnector",
    "PolygonTimeoutError",
    "PolygonTimespan",
    "PolygonWebsocketAuthFailedError",
    "PolygonWebsocketError",
    "PolygonWebsocketOverflowError",
    "PolygonWebsocketProtocolError",
    "PolygonWebsocketReconnectExhaustedError",
    "RealtimeStartRequest",
    "SymbolRealtimeContext",
]
