"""Unit tests for log context identifiers."""

from __future__ import annotations

from app.core.log_context import (
    LogContext,
    clear_log_context,
    generate_request_id,
    get_log_context,
    is_valid_context_id,
    normalize_context_id,
    reset_log_context,
    resolve_request_ids,
    set_log_context,
)


def test_generate_request_id_is_uuid_shaped() -> None:
    value = generate_request_id()
    assert is_valid_context_id(value)
    assert len(value) == 36


def test_rejects_control_characters_and_overlong_ids() -> None:
    assert normalize_context_id("abc\ndef") is None
    assert normalize_context_id("x" * 129) is None
    assert normalize_context_id("ok-id_1") == "ok-id_1"
    assert normalize_context_id(" has spaces ") is None


def test_request_id_generated_when_missing() -> None:
    ctx = resolve_request_ids(
        request_id_header=None,
        correlation_id_header=None,
        causation_id_header=None,
    )
    assert ctx.request_id is not None
    assert is_valid_context_id(ctx.request_id)


def test_correlation_id_defaults_to_request_id() -> None:
    ctx = resolve_request_ids(
        request_id_header=None,
        correlation_id_header=None,
        causation_id_header=None,
    )
    assert ctx.correlation_id == ctx.request_id
    assert ctx.causation_id is None


def test_incoming_valid_request_id_preserved() -> None:
    ctx = resolve_request_ids(
        request_id_header="req-111",
        correlation_id_header="corr-222",
        causation_id_header="cause-333",
    )
    assert ctx == LogContext(
        request_id="req-111",
        correlation_id="corr-222",
        causation_id="cause-333",
    )


def test_invalid_request_id_regenerated_causation_optional() -> None:
    ctx = resolve_request_ids(
        request_id_header="bad id!",
        correlation_id_header=None,
        causation_id_header="also bad!",
    )
    assert ctx.request_id is not None
    assert is_valid_context_id(ctx.request_id)
    assert ctx.request_id != "bad id!"
    assert ctx.correlation_id == ctx.request_id
    assert ctx.causation_id is None


def test_context_cleared_and_does_not_leak() -> None:
    clear_log_context()
    assert get_log_context() == LogContext()
    token = set_log_context(LogContext(request_id="a", correlation_id="a", causation_id="c"))
    assert get_log_context().request_id == "a"
    reset_log_context(token)
    assert get_log_context() == LogContext()
    clear_log_context()
    assert get_log_context().request_id is None
