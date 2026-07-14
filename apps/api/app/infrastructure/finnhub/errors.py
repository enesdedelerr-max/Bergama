"""Typed Finnhub connector errors (Issue #304A)."""

from __future__ import annotations


class FinnhubError(Exception):
    code: str = "finnhub.provider_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        self.code = code or self.code
        super().__init__(message)


class FinnhubNotConfiguredError(FinnhubError):
    code = "finnhub.not_configured"


class FinnhubInvalidRequestError(FinnhubError):
    code = "finnhub.invalid_request"


class FinnhubAuthenticationFailedError(FinnhubError):
    code = "finnhub.authentication_failed"


class FinnhubForbiddenError(FinnhubError):
    code = "finnhub.forbidden"


class FinnhubNotFoundError(FinnhubError):
    code = "finnhub.not_found"


class FinnhubRateLimitedError(FinnhubError):
    code = "finnhub.rate_limited"


class FinnhubTimeoutError(FinnhubError):
    code = "finnhub.timeout"


class FinnhubConnectionFailedError(FinnhubError):
    code = "finnhub.connection_failed"


class FinnhubProviderError(FinnhubError):
    code = "finnhub.provider_error"


class FinnhubInvalidResponseError(FinnhubError):
    code = "finnhub.invalid_response"


class FinnhubMappingFailedError(FinnhubError):
    code = "finnhub.mapping_failed"
