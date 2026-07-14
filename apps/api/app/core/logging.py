"""Structured logging configuration for the FastAPI runtime (Issue #203).

Uses the standard library only: JSON formatter, Filter, contextvars.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import UTC, datetime
from typing import Final

from app.core.config import AppSettings
from app.core.environment import AppEnvironment
from app.core.log_context import get_log_context

# Process-level fields bound at configure_logging time.
_service_name: str = "bergama-api"
_environment: str = "local"
_app_version: str = "0.0.0"
_configured: bool = False
_include_exception_stacks: bool = True

_SENSITIVE_KEY_PATTERN: Final = re.compile(
    r"("
    r"password|passwd|secret|token|authorization|api[_-]?key|api-key|"
    r"access[_-]?token|refresh[_-]?token|private[_-]?key|signing[_-]?key|"
    r"client[_-]?secret|cookie|set-cookie|session|credential|bearer|"
    r"app_secret_key|bootstrap_jwt_signing_key"
    r")",
    re.IGNORECASE,
)

_REDACTED: Final = "[REDACTED]"

# Known structured fields copied from LogRecord onto JSON/console output.
_STRUCTURED_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "event",
        "error_type",
        "error_code",
        "method",
        "path",
        "status_code",
        "duration_ms",
        "source",
        "version",
        "service",
        "environment",
    }
)

_UVICORN_LOGGERS: Final[tuple[str, ...]] = (
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
)


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def is_sensitive_key(key: str) -> bool:
    """Return True when a key name should be redacted."""
    # Boolean configuration indicators must remain visible in ops logs.
    if key.endswith("_configured"):
        return False
    return bool(_SENSITIVE_KEY_PATTERN.search(key))


def redact_value(key: str, value: object) -> object:
    """Redact sensitive values; recursively walk mappings and sequences."""
    if is_sensitive_key(key):
        return _REDACTED
    if isinstance(value, dict):
        return {str(k): redact_value(str(k), v) for k, v in value.items()}
    if isinstance(value, list):
        return [
            redact_mapping(item) if isinstance(item, dict) else redact_value(key, item)
            for item in value
        ]
    if isinstance(value, tuple):
        return tuple(
            redact_mapping(item) if isinstance(item, dict) else redact_value(key, item)
            for item in value
        )
    return value


def redact_mapping(data: dict[str, object]) -> dict[str, object]:
    """Return a copy of ``data`` with sensitive keys redacted (input unchanged)."""
    return {str(k): redact_value(str(k), v) for k, v in data.items()}


def use_json_logs(settings: AppSettings) -> bool:
    """Derive log format from environment: staging/production → JSON."""
    return settings.environment in {
        AppEnvironment.STAGING,
        AppEnvironment.PRODUCTION,
    }


def use_color_logs(settings: AppSettings) -> bool:
    """Color only for local interactive terminals."""
    if settings.environment is not AppEnvironment.LOCAL:
        return False
    return sys.stdout.isatty()


def include_exception_stacks(settings: AppSettings) -> bool:
    """Stack traces in logs for non-production; production keeps class/message only."""
    return settings.environment is not AppEnvironment.PRODUCTION


class ContextFilter(logging.Filter):
    """Inject process and request context onto every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        ctx = get_log_context()
        record.service = _service_name
        record.environment = _environment
        record.app_version = _app_version
        record.request_id = ctx.request_id
        record.correlation_id = ctx.correlation_id
        record.causation_id = ctx.causation_id
        return True


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per line (UTC ISO-8601, sorted keys)."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": _utc_timestamp(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": getattr(record, "service", _service_name),
            "environment": getattr(record, "environment", _environment),
            "app_version": getattr(record, "app_version", _app_version),
        }

        for field in (
            "request_id",
            "correlation_id",
            "causation_id",
            "event",
            "error_type",
            "error_code",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "source",
            "version",
        ):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info and _include_exception_stacks:
            payload["exception"] = self.formatException(record.exc_info)
        elif record.exc_info:
            exc_type = record.exc_info[0]
            payload["error_type"] = getattr(record, "error_type", None) or (
                exc_type.__name__ if exc_type is not None else "Exception"
            )

        extra_fields = getattr(record, "structured_fields", None)
        if isinstance(extra_fields, dict):
            for key, value in redact_mapping(extra_fields).items():
                if key not in payload and value is not None:
                    payload[key] = value

        return json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)


class ConsoleFormatter(logging.Formatter):
    """Human-readable console format preserving core request context."""

    def __init__(self, *, use_color: bool = False) -> None:
        super().__init__()
        self._use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        level = record.levelname
        if self._use_color:
            level = _colorize_level(level)

        parts = [
            _utc_timestamp(),
            level,
            record.name,
            record.getMessage(),
        ]

        request_id = getattr(record, "request_id", None)
        correlation_id = getattr(record, "correlation_id", None)
        if request_id:
            parts.append(f"request_id={request_id}")
        if correlation_id and correlation_id != request_id:
            parts.append(f"correlation_id={correlation_id}")

        event = getattr(record, "event", None)
        if event:
            parts.append(f"event={event}")

        status_code = getattr(record, "status_code", None)
        if status_code is not None:
            parts.append(f"status={status_code}")

        duration_ms = getattr(record, "duration_ms", None)
        if duration_ms is not None:
            parts.append(f"duration_ms={duration_ms}")

        line = " ".join(parts)
        if record.exc_info and _include_exception_stacks:
            line = f"{line}\n{self.formatException(record.exc_info)}"
        return line


_LEVEL_COLORS: Final[dict[str, str]] = {
    "DEBUG": "\033[36m",
    "INFO": "\033[32m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[35m",
}
_RESET: Final = "\033[0m"


def _colorize_level(level: str) -> str:
    color = _LEVEL_COLORS.get(level)
    if not color:
        return level
    return f"{color}{level}{_RESET}"


def structured_extra(**fields: object) -> dict[str, object]:
    """Build a logging ``extra`` dict with redacted structured fields.

    Known keys become LogRecord attributes for formatters; remaining keys
    are nested under ``structured_fields``.
    """
    redacted = redact_mapping(fields)
    known: dict[str, object] = {}
    other: dict[str, object] = {}
    for key, value in redacted.items():
        if key in _STRUCTURED_FIELDS or key in {
            "request_id",
            "correlation_id",
            "causation_id",
        }:
            known[key] = value
        else:
            other[key] = value
    if other:
        known["structured_fields"] = other
    return known


def get_logger(name: str) -> logging.Logger:
    """Return a named application logger."""
    return logging.getLogger(name)


def log_exception(
    logger: logging.Logger,
    message: str,
    exc: BaseException,
    *,
    level: int = logging.ERROR,
    error_code: str | None = None,
    **fields: object,
) -> None:
    """Log an exception with safe classification fields (no secret payloads)."""
    extra = structured_extra(
        error_type=type(exc).__name__,
        error_code=error_code,
        **fields,
    )
    logger.log(level, message, exc_info=exc, extra=extra)


def configure_logging(settings: AppSettings) -> None:
    """Configure process-wide logging from AppSettings.

    Idempotent: clears root/uvicorn handlers then attaches exactly one root handler.
    Safe to call repeatedly from tests. Does not load settings at import time.
    """
    global _service_name, _environment, _app_version, _configured, _include_exception_stacks

    _service_name = settings.service_name
    _environment = settings.environment.value
    _app_version = settings.app_version
    _include_exception_stacks = include_exception_stacks(settings)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(settings.log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(ContextFilter())

    if use_json_logs(settings):
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(ConsoleFormatter(use_color=use_color_logs(settings)))

    root.addHandler(handler)

    for name in (*_UVICORN_LOGGERS, "httpx", "httpcore"):
        named = logging.getLogger(name)
        named.handlers.clear()
        named.propagate = True
        named.setLevel(settings.log_level)

    # Request middleware owns HTTP lifecycle logs; keep access quieter.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    _configured = True


def is_logging_configured() -> bool:
    """Return whether configure_logging has been called in this process."""
    return _configured


def root_handler_count() -> int:
    """Return the number of handlers on the root logger (test helper)."""
    return len(logging.getLogger().handlers)
