"""Finnhub REST infrastructure (Issue #304A) — profile + basic financials only.

Health check intentionally omitted: no safe zero/low-cost Finnhub probe is
documented for readiness without consuming authenticated quota. Configuration
validation remains settings-side (`FinnhubSettings`) and must not be labeled
provider health.

Series time-history from `/stock/metric` is not mapped in #304A.
"""

from __future__ import annotations

from app.infrastructure.finnhub.errors import (
    FinnhubAuthenticationFailedError,
    FinnhubConnectionFailedError,
    FinnhubError,
    FinnhubForbiddenError,
    FinnhubInvalidRequestError,
    FinnhubInvalidResponseError,
    FinnhubMappingFailedError,
    FinnhubNotConfiguredError,
    FinnhubNotFoundError,
    FinnhubProviderError,
    FinnhubRateLimitedError,
    FinnhubTimeoutError,
)
from app.infrastructure.finnhub.fundamentals import (
    FinnhubFundamentalsConnector,
    FundamentalsRequest,
    FundamentalsResult,
)
from app.infrastructure.finnhub.http import FinnhubHttpClient
from app.infrastructure.finnhub.mapper import METRIC_DEFINITIONS, SUPPORTED_METRICS
from app.infrastructure.finnhub.reference import FinnhubReferenceConnector, ReferenceRequest

__all__ = [
    "METRIC_DEFINITIONS",
    "SUPPORTED_METRICS",
    "FinnhubAuthenticationFailedError",
    "FinnhubConnectionFailedError",
    "FinnhubError",
    "FinnhubForbiddenError",
    "FinnhubFundamentalsConnector",
    "FinnhubHttpClient",
    "FinnhubInvalidRequestError",
    "FinnhubInvalidResponseError",
    "FinnhubMappingFailedError",
    "FinnhubNotConfiguredError",
    "FinnhubNotFoundError",
    "FinnhubProviderError",
    "FinnhubRateLimitedError",
    "FinnhubReferenceConnector",
    "FinnhubTimeoutError",
    "FundamentalsRequest",
    "FundamentalsResult",
    "ReferenceRequest",
]
