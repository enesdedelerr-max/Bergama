"""FRED REST infrastructure (Issue #304B) — series metadata + observations only.

Health check intentionally omitted: every FRED API call requires an API key and
consumes quota; there is no documented cheap, honest non-data probe. Configuration
validation remains settings-side (`FredSettings`) and must not be labeled provider
health.

Frequency aggregation and unit transformations are out of scope for #304B.
"""

from __future__ import annotations

from app.infrastructure.fred.errors import (
    FredAuthenticationFailedError,
    FredConnectionFailedError,
    FredError,
    FredForbiddenError,
    FredInvalidRequestError,
    FredInvalidResponseError,
    FredMappingFailedError,
    FredNotConfiguredError,
    FredNotFoundError,
    FredPaginationLimitError,
    FredPaginationStateError,
    FredProviderError,
    FredRateLimitedError,
    FredTimeoutError,
)
from app.infrastructure.fred.http import FredHttpClient
from app.infrastructure.fred.mapper import (
    CANONICAL_FREQUENCIES,
    FREQUENCY_DEFINITIONS,
    SeriesMetadataView,
)
from app.infrastructure.fred.observations import (
    FredObservationsConnector,
    ObservationsRequest,
    ObservationsResult,
)
from app.infrastructure.fred.series import FredSeriesConnector, SeriesRequest

__all__ = [
    "CANONICAL_FREQUENCIES",
    "FREQUENCY_DEFINITIONS",
    "FredAuthenticationFailedError",
    "FredConnectionFailedError",
    "FredError",
    "FredForbiddenError",
    "FredHttpClient",
    "FredInvalidRequestError",
    "FredInvalidResponseError",
    "FredMappingFailedError",
    "FredNotConfiguredError",
    "FredNotFoundError",
    "FredObservationsConnector",
    "FredPaginationLimitError",
    "FredPaginationStateError",
    "FredProviderError",
    "FredRateLimitedError",
    "FredSeriesConnector",
    "FredTimeoutError",
    "ObservationsRequest",
    "ObservationsResult",
    "SeriesMetadataView",
    "SeriesRequest",
]
