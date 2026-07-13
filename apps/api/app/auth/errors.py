"""Stable authentication error contract (Issue #205)."""

from __future__ import annotations

from typing import Final

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.log_context import get_log_context
from app.core.logging import get_logger, structured_extra

logger = get_logger(__name__)

WWW_AUTHENTICATE_BEARER: Final = "Bearer"


class AuthError(Exception):
    """Application auth failure with stable machine-readable code."""

    def __init__(self, code: str, message: str, *, status_code: int = 401) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def auth_error_response(error: AuthError) -> JSONResponse:
    """Build a safe auth error body; never include tokens or keys."""
    ctx = get_log_context()
    headers: dict[str, str] = {}
    if error.status_code == 401:
        headers["WWW-Authenticate"] = WWW_AUTHENTICATE_BEARER
    return JSONResponse(
        status_code=error.status_code,
        content={
            "code": error.code,
            "message": error.message,
            "request_id": ctx.request_id,
        },
        headers=headers,
    )


async def auth_error_handler(_request: Request, exc: AuthError) -> JSONResponse:
    """Map AuthError to HTTP without leaking token material."""
    logger.warning(
        "authentication rejected",
        extra=structured_extra(
            event="auth.token.rejected",
            error_code=exc.code,
            source="auth",
        ),
    )
    return auth_error_response(exc)


MISSING_TOKEN = AuthError(
    code="auth.missing_token",
    message="Authentication credentials were not provided.",
)
INVALID_TOKEN = AuthError(
    code="auth.invalid_token",
    message="Authentication credentials are invalid.",
)
EXPIRED_TOKEN = AuthError(
    code="auth.expired_token",
    message="Authentication credentials have expired.",
)
INVALID_ISSUER = AuthError(
    code="auth.invalid_issuer",
    message="Authentication credentials are invalid.",
)
INVALID_AUDIENCE = AuthError(
    code="auth.invalid_audience",
    message="Authentication credentials are invalid.",
)
INVALID_TOKEN_TYPE = AuthError(
    code="auth.invalid_token_type",
    message="Authentication credentials are invalid.",
)
BOOTSTRAP_DISABLED = AuthError(
    code="auth.bootstrap_disabled",
    message="Bootstrap authentication is not available.",
    status_code=404,
)
