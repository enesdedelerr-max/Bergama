"""Typed FRED connector errors (Issue #304B)."""

from __future__ import annotations


class FredError(Exception):
    code: str = "fred.provider_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class FredNotConfiguredError(FredError):
    code = "fred.not_configured"


class FredInvalidRequestError(FredError):
    code = "fred.invalid_request"


class FredAuthenticationFailedError(FredError):
    code = "fred.authentication_failed"


class FredForbiddenError(FredError):
    code = "fred.forbidden"


class FredNotFoundError(FredError):
    code = "fred.not_found"


class FredRateLimitedError(FredError):
    code = "fred.rate_limited"


class FredTimeoutError(FredError):
    code = "fred.timeout"


class FredConnectionFailedError(FredError):
    code = "fred.connection_failed"


class FredProviderError(FredError):
    code = "fred.provider_error"


class FredInvalidResponseError(FredError):
    code = "fred.invalid_response"


class FredMappingFailedError(FredError):
    code = "fred.mapping_failed"


class FredPaginationLimitError(FredError):
    code = "fred.pagination_limit"


class FredPaginationStateError(FredError):
    code = "fred.pagination_state"
