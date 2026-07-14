"""Typed Polygon connector errors (Issue #302)."""

from __future__ import annotations


class PolygonError(Exception):
    """Base Polygon connector error."""

    code: str = "polygon.provider_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        self.code = code or self.code
        super().__init__(message)


class PolygonNotConfiguredError(PolygonError):
    code = "polygon.not_configured"


class PolygonInvalidRequestError(PolygonError):
    code = "polygon.invalid_request"


class PolygonAuthenticationFailedError(PolygonError):
    code = "polygon.authentication_failed"


class PolygonForbiddenError(PolygonError):
    code = "polygon.forbidden"


class PolygonNotFoundError(PolygonError):
    code = "polygon.not_found"


class PolygonRateLimitedError(PolygonError):
    code = "polygon.rate_limited"


class PolygonTimeoutError(PolygonError):
    code = "polygon.timeout"


class PolygonConnectionFailedError(PolygonError):
    code = "polygon.connection_failed"


class PolygonProviderError(PolygonError):
    code = "polygon.provider_error"


class PolygonInvalidResponseError(PolygonError):
    code = "polygon.invalid_response"


class PolygonPaginationLoopError(PolygonError):
    code = "polygon.pagination_loop"


class PolygonPaginationLimitError(PolygonError):
    code = "polygon.pagination_limit"


class PolygonMappingFailedError(PolygonError):
    code = "polygon.mapping_failed"
