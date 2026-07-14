"""Benzinga Newsfeed REST infrastructure (Issue #304D).

Health check intentionally omitted: every Newsfeed call requires an API key and
consumes entitled quota; there is no documented cheap, honest non-data probe.
Configuration validation remains settings-side (`BenzingaSettings`) and must not
be labeled provider health.

Channels catalog, news-removed, WebSocket/TCP, body scraping, and Kafka/Iceberg
are out of scope for #304D.
"""

from __future__ import annotations

from app.infrastructure.benzinga.errors import (
    BenzingaAuthenticationFailedError,
    BenzingaConnectionFailedError,
    BenzingaEntitlementRequiredError,
    BenzingaError,
    BenzingaForbiddenError,
    BenzingaInvalidRequestError,
    BenzingaInvalidResponseError,
    BenzingaMappingFailedError,
    BenzingaNotConfiguredError,
    BenzingaNotFoundError,
    BenzingaPaginationLimitError,
    BenzingaPaginationLoopError,
    BenzingaProviderError,
    BenzingaRateLimitedError,
    BenzingaTimeoutError,
)
from app.infrastructure.benzinga.http import BenzingaHttpClient
from app.infrastructure.benzinga.mapper import (
    ALLOWED_URL_HOSTS,
    TIME_POLICY,
    normalize_ticker_for_lookup,
)
from app.infrastructure.benzinga.news import BenzingaNewsConnector, NewsRequest, NewsResult

__all__ = [
    "ALLOWED_URL_HOSTS",
    "TIME_POLICY",
    "BenzingaAuthenticationFailedError",
    "BenzingaConnectionFailedError",
    "BenzingaEntitlementRequiredError",
    "BenzingaError",
    "BenzingaForbiddenError",
    "BenzingaHttpClient",
    "BenzingaInvalidRequestError",
    "BenzingaInvalidResponseError",
    "BenzingaMappingFailedError",
    "BenzingaNewsConnector",
    "BenzingaNotConfiguredError",
    "BenzingaNotFoundError",
    "BenzingaPaginationLimitError",
    "BenzingaPaginationLoopError",
    "BenzingaProviderError",
    "BenzingaRateLimitedError",
    "BenzingaTimeoutError",
    "NewsRequest",
    "NewsResult",
    "normalize_ticker_for_lookup",
]
