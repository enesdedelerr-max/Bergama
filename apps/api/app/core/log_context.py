"""Request-scoped logging context via contextvars."""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Final
from uuid import uuid4

HEADER_REQUEST_ID: Final = "x-request-id"
HEADER_CORRELATION_ID: Final = "x-correlation-id"
HEADER_CAUSATION_ID: Final = "x-causation-id"

RESPONSE_HEADER_REQUEST_ID: Final = "X-Request-ID"
RESPONSE_HEADER_CORRELATION_ID: Final = "X-Correlation-ID"
RESPONSE_HEADER_CAUSATION_ID: Final = "X-Causation-ID"

# Cap inbound header length to prevent log injection / abuse.
_MAX_ID_LENGTH: Final = 128
_ALLOWED_ID_CHARS: Final = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)


@dataclass(frozen=True, slots=True)
class LogContext:
    """Immutable snapshot of request correlation identifiers."""

    request_id: str | None = None
    correlation_id: str | None = None
    causation_id: str | None = None


_log_context: ContextVar[LogContext | None] = ContextVar(
    "bergama_log_context",
    default=None,
)


def get_log_context() -> LogContext:
    """Return the current request log context."""
    current = _log_context.get()
    return current if current is not None else LogContext()


def set_log_context(context: LogContext) -> Token[LogContext | None]:
    """Bind log context for the current task; returns a reset token."""
    return _log_context.set(context)


def reset_log_context(token: Token[LogContext | None]) -> None:
    """Restore prior log context from a set token."""
    _log_context.reset(token)


def clear_log_context() -> None:
    """Clear request context (empty snapshot)."""
    _log_context.set(None)


def generate_request_id() -> str:
    """Generate a new request identifier."""
    return str(uuid4())


def is_valid_context_id(value: str | None) -> bool:
    """Return True when value is a safe, bounded correlation-style identifier."""
    if value is None:
        return False
    if not value or len(value) > _MAX_ID_LENGTH:
        return False
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        return False
    return all(ch in _ALLOWED_ID_CHARS for ch in value)


def normalize_context_id(value: str | None) -> str | None:
    """Validate and return a context ID, or None when invalid/missing."""
    if value is None:
        return None
    candidate = value.strip()
    if not is_valid_context_id(candidate):
        return None
    return candidate


def resolve_request_ids(
    *,
    request_id_header: str | None,
    correlation_id_header: str | None,
    causation_id_header: str | None,
) -> LogContext:
    """Resolve inbound headers into a safe LogContext.

    Policy:
    - Invalid/missing request_id → generate UUID.
    - Invalid/missing correlation_id → default to request_id.
    - Invalid/missing causation_id → omit (do not invent).
    """
    request_id = normalize_context_id(request_id_header) or generate_request_id()
    correlation_id = normalize_context_id(correlation_id_header) or request_id
    causation_id = normalize_context_id(causation_id_header)
    return LogContext(
        request_id=request_id,
        correlation_id=correlation_id,
        causation_id=causation_id,
    )
