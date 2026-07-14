"""HTTP request context and structured request lifecycle logging."""

from __future__ import annotations

import json
import logging
import time
from typing import Final

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.log_context import (
    RESPONSE_HEADER_CAUSATION_ID,
    RESPONSE_HEADER_CORRELATION_ID,
    RESPONSE_HEADER_REQUEST_ID,
    LogContext,
    reset_log_context,
    resolve_request_ids,
    set_log_context,
)
from app.core.logging import get_logger, structured_extra

logger = get_logger(__name__)

_HEADER_REQUEST_ID: Final = "x-request-id"
_HEADER_CORRELATION_ID: Final = "x-correlation-id"
_HEADER_CAUSATION_ID: Final = "x-causation-id"

# Probe paths use DEBUG for start/complete to reduce noise; failures stay loud.
_QUIET_PATHS: Final[frozenset[str]] = frozenset({"/health", "/ready"})


class RequestContextMiddleware:
    """Bind request IDs, emit lifecycle logs, and clear context after each request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        context = resolve_request_ids(
            request_id_header=headers.get(_HEADER_REQUEST_ID),
            correlation_id_header=headers.get(_HEADER_CORRELATION_ID),
            causation_id_header=headers.get(_HEADER_CAUSATION_ID),
        )
        token = set_log_context(context)

        method = str(scope.get("method", "UNKNOWN"))
        path = str(scope.get("path", ""))
        quiet = path in _QUIET_PATHS
        start_level = logging.DEBUG if quiet else logging.INFO
        started = time.monotonic()
        status_code_holder: dict[str, int] = {"value": 500}
        response_started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
                status_code_holder["value"] = int(message["status"])
                response_headers = MutableHeaders(scope=message)
                _apply_context_headers(response_headers, context)
            await send(message)

        try:
            logger.log(
                start_level,
                "http request started",
                extra=structured_extra(
                    event="http.request.started",
                    method=method,
                    path=path,
                    source="middleware",
                ),
            )
            try:
                await self.app(scope, receive, send_wrapper)
            except Exception as exc:
                duration_ms = _duration_ms(started)
                logger.error(
                    "http request failed",
                    exc_info=exc,
                    extra=structured_extra(
                        event="http.request.failed",
                        method=method,
                        path=path,
                        status_code=status_code_holder["value"],
                        duration_ms=duration_ms,
                        error_type=type(exc).__name__,
                        source="middleware",
                    ),
                )
                if not response_started:
                    await _send_safe_error(send, context)
                    return
                raise
            except BaseException as exc:
                duration_ms = _duration_ms(started)
                logger.warning(
                    "http request cancelled or interrupted",
                    extra=structured_extra(
                        event="http.request.failed",
                        method=method,
                        path=path,
                        duration_ms=duration_ms,
                        error_type=type(exc).__name__,
                        source="middleware",
                    ),
                )
                raise
            else:
                duration_ms = _duration_ms(started)
                complete_level = logging.DEBUG if quiet else logging.INFO
                logger.log(
                    complete_level,
                    "http request completed",
                    extra=structured_extra(
                        event="http.request.completed",
                        method=method,
                        path=path,
                        status_code=status_code_holder["value"],
                        duration_ms=duration_ms,
                        source="middleware",
                    ),
                )
        finally:
            reset_log_context(token)


def _apply_context_headers(response_headers: MutableHeaders, context: LogContext) -> None:
    assert context.request_id is not None
    assert context.correlation_id is not None
    response_headers[RESPONSE_HEADER_REQUEST_ID] = context.request_id
    response_headers[RESPONSE_HEADER_CORRELATION_ID] = context.correlation_id
    if context.causation_id is not None:
        response_headers[RESPONSE_HEADER_CAUSATION_ID] = context.causation_id


async def _send_safe_error(send: Send, context: LogContext) -> None:
    """Return a safe 500 when an exception escapes before a response starts."""
    assert context.request_id is not None
    assert context.correlation_id is not None
    payload = json.dumps(
        {
            "code": "internal.error",
            "message": "An unexpected error occurred.",
            "request_id": context.request_id,
        }
    ).encode("utf-8")
    headers = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(payload)).encode("ascii")),
        (RESPONSE_HEADER_REQUEST_ID.encode("latin-1"), context.request_id.encode("latin-1")),
        (
            RESPONSE_HEADER_CORRELATION_ID.encode("latin-1"),
            context.correlation_id.encode("latin-1"),
        ),
    ]
    if context.causation_id is not None:
        headers.append(
            (
                RESPONSE_HEADER_CAUSATION_ID.encode("latin-1"),
                context.causation_id.encode("latin-1"),
            )
        )
    await send({"type": "http.response.start", "status": 500, "headers": headers})
    await send({"type": "http.response.body", "body": payload})


def _duration_ms(started: float) -> float:
    return round((time.monotonic() - started) * 1000, 3)
