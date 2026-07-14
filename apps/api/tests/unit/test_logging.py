"""Unit tests for structured logging configuration and redaction."""

from __future__ import annotations

import json
import logging
from copy import deepcopy
from datetime import datetime
from io import StringIO

import pytest
from app.core.config import AppSettings
from app.core.environment import AppEnvironment
from app.core.log_context import LogContext, reset_log_context, set_log_context
from app.core.logging import (
    ConsoleFormatter,
    ContextFilter,
    JsonFormatter,
    configure_logging,
    get_logger,
    is_sensitive_key,
    log_exception,
    redact_mapping,
    root_handler_count,
    structured_extra,
    use_color_logs,
    use_json_logs,
)
from app.lifespan import on_startup
from tests.conftest import make_production_secrets


@pytest.fixture
def capture_handler() -> tuple[logging.Handler, StringIO]:
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.addFilter(ContextFilter())
    handler.setFormatter(JsonFormatter())
    return handler, stream


def test_use_json_logs_by_environment() -> None:
    assert use_json_logs(AppSettings(environment=AppEnvironment.LOCAL)) is False
    assert use_json_logs(AppSettings(environment=AppEnvironment.TEST)) is False
    assert (
        use_json_logs(
            AppSettings(
                environment=AppEnvironment.STAGING,
                debug=False,
                secrets=make_production_secrets(),
            )
        )
        is True
    )
    assert (
        use_json_logs(
            AppSettings(
                environment=AppEnvironment.PRODUCTION,
                debug=False,
                secrets=make_production_secrets(),
            )
        )
        is True
    )


def test_local_format_is_human_readable_production_is_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging(AppSettings(environment=AppEnvironment.LOCAL, log_level="INFO", debug=True))
    get_logger("test.local").info("local-line", extra=structured_extra(event="local.check"))
    local_line = capsys.readouterr().out.strip().splitlines()[-1]
    assert not local_line.startswith("{")
    assert "local-line" in local_line
    assert "event=local.check" in local_line

    configure_logging(
        AppSettings(
            environment=AppEnvironment.PRODUCTION,
            log_level="INFO",
            debug=False,
            secrets=make_production_secrets(),
        )
    )
    get_logger("test.prod").info("prod-line", extra=structured_extra(event="prod.check"))
    prod_line = capsys.readouterr().out.strip().splitlines()[-1]
    payload = json.loads(prod_line)
    assert payload["message"] == "prod-line"
    assert payload["event"] == "prod.check"


def test_use_color_logs_false_outside_local_tty() -> None:
    assert use_color_logs(AppSettings(environment=AppEnvironment.TEST)) is False
    assert (
        use_color_logs(
            AppSettings(
                environment=AppEnvironment.STAGING,
                debug=False,
                secrets=make_production_secrets(),
            )
        )
        is False
    )


def test_redaction_nested_does_not_mutate_and_preserves_safe_values() -> None:
    original = {
        "password": "secret",
        "passwd": "x",
        "api_key": "k",
        "api-key": "k2",
        "authorization": "Bearer x",
        "cookie": "c",
        "session": "s",
        "credential": "cred",
        "nested": {"token": "abc", "symbol": "AAPL"},
        "items": [{"secret": "s", "qty": 1}],
        "path": "/orders",
    }
    before = deepcopy(original)
    payload = redact_mapping(original)
    assert original == before
    assert payload["password"] == "[REDACTED]"
    assert payload["passwd"] == "[REDACTED]"
    assert payload["api_key"] == "[REDACTED]"
    assert payload["api-key"] == "[REDACTED]"
    assert payload["authorization"] == "[REDACTED]"
    assert payload["cookie"] == "[REDACTED]"
    assert payload["session"] == "[REDACTED]"
    assert payload["credential"] == "[REDACTED]"
    assert payload["nested"]["token"] == "[REDACTED]"
    assert payload["nested"]["symbol"] == "AAPL"
    assert payload["items"][0]["secret"] == "[REDACTED]"
    assert payload["items"][0]["qty"] == 1
    assert payload["path"] == "/orders"
    assert is_sensitive_key("secret")
    assert not is_sensitive_key("path")


def test_json_formatter_outputs_valid_json_with_required_fields_and_utc(
    capture_handler: tuple[logging.Handler, StringIO],
) -> None:
    handler, stream = capture_handler
    configure_logging(
        AppSettings(
            environment=AppEnvironment.STAGING,
            log_level="INFO",
            service_name="bergama-api",
            app_version="0.2.0",
            debug=False,
            secrets=make_production_secrets(),
        )
    )
    logger = get_logger("test.json")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    token = set_log_context(LogContext(request_id="r1", correlation_id="c1", causation_id=None))
    try:
        logger.info(
            "hello",
            extra=structured_extra(event="unit.test", method="GET", path="/x"),
        )
    finally:
        reset_log_context(token)
        logger.handlers.clear()

    payload = json.loads(stream.getvalue().strip())
    assert payload["message"] == "hello"
    assert payload["event"] == "unit.test"
    assert payload["request_id"] == "r1"
    assert payload["correlation_id"] == "c1"
    assert "causation_id" not in payload
    assert payload["level"] == "INFO"
    assert payload["logger"] == "test.json"
    assert payload["service"] == "bergama-api"
    assert payload["environment"] == "staging"
    assert payload["app_version"] == "0.2.0"
    # UTC ISO-8601 with Z suffix.
    ts = payload["timestamp"]
    assert isinstance(ts, str) and ts.endswith("Z")
    datetime.fromisoformat(ts.replace("Z", "+00:00"))


def test_json_output_is_one_object_per_line_and_sorted(
    capture_handler: tuple[logging.Handler, StringIO],
) -> None:
    handler, stream = capture_handler
    logger = get_logger("test.sorted")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    logger.info("line-a", extra=structured_extra(event="a"))
    logger.info("line-b", extra=structured_extra(event="b"))
    logger.handlers.clear()

    lines = [line for line in stream.getvalue().splitlines() if line]
    assert len(lines) == 2
    for line in lines:
        parsed = json.loads(line)
        assert list(parsed.keys()) == sorted(parsed.keys())


def test_log_level_follows_settings(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(AppSettings(environment=AppEnvironment.TEST, log_level="ERROR", debug=False))
    get_logger("test.level").info("should-not-appear")
    get_logger("test.level").error("should-appear")
    out = capsys.readouterr().out
    assert "should-not-appear" not in out
    assert "should-appear" in out


def test_configure_logging_is_idempotent_no_duplicate_handlers() -> None:
    settings = AppSettings(environment=AppEnvironment.TEST, log_level="INFO", debug=False)
    configure_logging(settings)
    configure_logging(settings)
    configure_logging(settings)
    assert root_handler_count() == 1
    assert len(logging.getLogger("uvicorn").handlers) == 0
    assert len(logging.getLogger("uvicorn.error").handlers) == 0
    assert len(logging.getLogger("uvicorn.access").handlers) == 0
    assert logging.getLogger("uvicorn.error").propagate is True


def test_console_formatter_includes_request_context() -> None:
    record = logging.LogRecord(
        name="test.console",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="ping",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-9"
    record.correlation_id = "corr-9"
    record.event = "http.request.completed"
    record.status_code = 200
    record.duration_ms = 1.5

    line = ConsoleFormatter(use_color=False).format(record)
    assert "ping" in line
    assert "request_id=req-9" in line
    assert "correlation_id=corr-9" in line
    assert "event=http.request.completed" in line
    assert "status=200" in line
    assert "\033[" not in line


@pytest.mark.asyncio
async def test_startup_logs_do_not_expose_settings_secrets(
    capsys: pytest.CaptureFixture[str],
) -> None:
    settings = AppSettings(
        environment=AppEnvironment.STAGING,
        log_level="INFO",
        service_name="bergama-api",
        app_version="0.2.0",
        debug=False,
        secrets=make_production_secrets(),
    )
    configure_logging(settings)
    await on_startup(settings)
    lines = [line for line in capsys.readouterr().out.splitlines() if line.startswith("{")]
    payloads = [json.loads(line) for line in lines]
    events = {p["event"] for p in payloads}
    assert "application.starting" in events
    assert "application.started" in events
    for payload in payloads:
        dumped = json.dumps(payload)
        assert "prod-valid-app-secret-key-value-0001" not in dumped
        assert "model_dump" not in dumped
        assert "AppSettings" not in dumped
        assert payload.get("service") == "bergama-api"
        assert payload.get("version") == "0.2.0" or payload.get("app_version") == "0.2.0"
        assert payload.get("environment") == "staging"


def test_log_exception_includes_error_type(
    capture_handler: tuple[logging.Handler, StringIO],
) -> None:
    handler, stream = capture_handler
    configure_logging(
        AppSettings(
            environment=AppEnvironment.STAGING,
            log_level="ERROR",
            debug=False,
            secrets=make_production_secrets(),
        )
    )
    logger = get_logger("test.exc")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)
    logger.propagate = False

    try:
        raise ValueError("boom")
    except ValueError as exc:
        log_exception(logger, "failed", exc, error_code="unit.boom", event="unit.fail")

    logger.handlers.clear()
    payload = json.loads(stream.getvalue().strip())
    assert payload["error_type"] == "ValueError"
    assert payload["error_code"] == "unit.boom"
    assert "exception" in payload
    assert "boom" in payload["exception"]


def test_structured_extra_redacts_authorization() -> None:
    extra = structured_extra(authorization="Bearer secret", path="/x", event="e")
    assert extra["event"] == "e"
    assert extra["path"] == "/x"
    assert extra["structured_fields"]["authorization"] == "[REDACTED]"
