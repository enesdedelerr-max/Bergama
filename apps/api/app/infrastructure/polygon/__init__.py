"""Polygon REST infrastructure (Issue #302) — historical stocks bars only.

Health check intentionally omitted: no safe zero/low-cost Polygon probe is
documented for readiness without consuming authenticated quota. Configuration
validation remains settings-side (`PolygonSettings`) and must not be labeled
provider health.
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
)
from app.infrastructure.polygon.historical import (
    HistoricalBarsRequest,
    HistoricalBarsResult,
    PolygonHistoricalConnector,
    PolygonTimespan,
)
from app.infrastructure.polygon.http import PolygonHttpClient
from app.infrastructure.polygon.protocol import HistoricalBarConnector

__all__ = [
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
    "PolygonTimeoutError",
    "PolygonTimespan",
]
