"""Typed SEC EDGAR connector errors (Issue #304C)."""

from __future__ import annotations


class SecError(Exception):
    code: str = "sec.provider_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class SecNotConfiguredError(SecError):
    code = "sec.not_configured"


class SecInvalidRequestError(SecError):
    code = "sec.invalid_request"


class SecForbiddenError(SecError):
    code = "sec.forbidden"


class SecNotFoundError(SecError):
    code = "sec.not_found"


class SecRateLimitedError(SecError):
    code = "sec.rate_limited"


class SecTimeoutError(SecError):
    code = "sec.timeout"


class SecConnectionFailedError(SecError):
    code = "sec.connection_failed"


class SecProviderError(SecError):
    code = "sec.provider_error"


class SecInvalidResponseError(SecError):
    code = "sec.invalid_response"


class SecMappingFailedError(SecError):
    code = "sec.mapping_failed"


class SecInvalidCikError(SecError):
    code = "sec.invalid_cik"
