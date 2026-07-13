"""Global exception handlers — safe API responses, structured logs."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.auth.errors import AuthError, auth_error_handler
from app.core.log_context import get_log_context
from app.core.logging import get_logger, structured_extra

logger = get_logger(__name__)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log unhandled errors; never put stack traces in the HTTP body."""
    ctx = get_log_context()
    logger.error(
        "unhandled exception",
        exc_info=exc,
        extra=structured_extra(
            event="http.exception.unhandled",
            error_type=type(exc).__name__,
            method=request.method,
            path=request.url.path,
            source="exception_handler",
        ),
    )
    return JSONResponse(
        status_code=500,
        content={
            "code": "internal.error",
            "message": "An unexpected error occurred.",
            "request_id": ctx.request_id,
        },
    )


def register_exception_handlers(application: FastAPI) -> None:
    """Register auth and unhandled-exception handlers."""
    application.add_exception_handler(AuthError, auth_error_handler)  # type: ignore[arg-type]
    application.add_exception_handler(Exception, unhandled_exception_handler)
