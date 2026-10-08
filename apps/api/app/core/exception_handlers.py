"""Global exception handlers — safe API responses, structured logs."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.auth.errors import AuthError, auth_error_handler
from app.core.log_context import get_log_context
from app.core.logging import get_logger, structured_extra
from app.intelligence_runs.product_errors import IntelligenceRunProductError

logger = get_logger(__name__)


async def intelligence_run_product_error_handler(
    _request: Request,
    exc: IntelligenceRunProductError,
) -> JSONResponse:
    """Map product errors without leaking storage internals or stack traces."""
    ctx = get_log_context()
    logger.warning(
        "intelligence run product error",
        extra=structured_extra(
            event="intelligence_runs.product_error",
            error_code=exc.code,
            source="exception_handler",
        ),
    )
    body: dict[str, object] = {
        "code": exc.code,
        "message": exc.message,
        "request_id": ctx.request_id,
    }
    if exc.details is not None:
        body["details"] = exc.details
    return JSONResponse(status_code=exc.status_code, content=body)


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
    """Register auth, product, and unhandled-exception handlers."""
    application.add_exception_handler(AuthError, auth_error_handler)  # type: ignore[arg-type]
    application.add_exception_handler(
        IntelligenceRunProductError,
        intelligence_run_product_error_handler,  # type: ignore[arg-type]
    )
    application.add_exception_handler(Exception, unhandled_exception_handler)
