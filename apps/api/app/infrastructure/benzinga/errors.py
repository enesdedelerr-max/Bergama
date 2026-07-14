"""Typed Benzinga connector errors (Issue #304D)."""

from __future__ import annotations


class BenzingaError(Exception):
    code: str = "benzinga.provider_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class BenzingaNotConfiguredError(BenzingaError):
    code = "benzinga.not_configured"


class BenzingaInvalidRequestError(BenzingaError):
    code = "benzinga.invalid_request"


class BenzingaAuthenticationFailedError(BenzingaError):
    code = "benzinga.authentication_failed"


class BenzingaEntitlementRequiredError(BenzingaError):
    code = "benzinga.entitlement_required"


class BenzingaForbiddenError(BenzingaError):
    code = "benzinga.forbidden"


class BenzingaNotFoundError(BenzingaError):
    code = "benzinga.not_found"


class BenzingaRateLimitedError(BenzingaError):
    code = "benzinga.rate_limited"


class BenzingaTimeoutError(BenzingaError):
    code = "benzinga.timeout"


class BenzingaConnectionFailedError(BenzingaError):
    code = "benzinga.connection_failed"


class BenzingaProviderError(BenzingaError):
    code = "benzinga.provider_error"


class BenzingaInvalidResponseError(BenzingaError):
    code = "benzinga.invalid_response"


class BenzingaPaginationLoopError(BenzingaError):
    code = "benzinga.pagination_loop"


class BenzingaPaginationLimitError(BenzingaError):
    code = "benzinga.pagination_limit"


class BenzingaMappingFailedError(BenzingaError):
    code = "benzinga.mapping_failed"
