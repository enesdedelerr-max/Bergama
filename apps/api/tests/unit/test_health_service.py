"""Unit tests for HealthService aggregation and policy."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime

import pytest
from app.core.clock import FixedClock
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.core.log_context import LogContext, reset_log_context, set_log_context
from app.health.protocol import ERROR_CHECK_TIMEOUT
from app.health.runtime_state import RuntimeState
from app.health.service import HealthService
from app.schemas.health import DependencyHealthResult, DependencyHealthStatus
from pydantic import ValidationError


@dataclass(slots=True)
class FakeCheck:
    name: str
    required: bool
    timeout_seconds: float = 1.0
    status: DependencyHealthStatus = DependencyHealthStatus.PASS
    message: str | None = "ok"
    error_code: str | None = None
    hang: bool = False
    raise_exc: Exception | None = None
    calls: int = field(default=0, init=False)

    async def check(self) -> DependencyHealthResult:
        self.calls += 1
        if self.raise_exc is not None:
            raise self.raise_exc
        if self.hang:
            await asyncio.Future()
        return DependencyHealthResult(
            name=self.name,
            status=self.status,
            required=self.required,
            latency_ms=1.0,
            message=self.message,
            error_code=self.error_code,
        )


def _settings(**overrides: object) -> AppSettings:
    base: dict[str, object] = {
        "environment": AppEnvironment.TEST,
        "debug": False,
        "service_name": "bergama-api-test",
        "app_version": "0.2.0",
        "bootstrap_auth_enabled": False,
        "health_check_timeout_seconds": 0.2,
        "health_total_timeout_seconds": 1.0,
    }
    base.update(overrides)
    return AppSettings(**base)  # type: ignore[arg-type]


def _service(*checks: FakeCheck, settings: AppSettings | None = None) -> HealthService:
    resolved = settings or _settings()
    runtime = RuntimeState()
    runtime.mark_started()
    return HealthService(
        settings=resolved,
        clock=FixedClock(datetime(2026, 7, 12, 12, 0, 0, tzinfo=UTC)),
        runtime_state=runtime,
        checks=checks,
    )


@pytest.mark.asyncio
async def test_liveness_never_calls_external_checks() -> None:
    check = FakeCheck(name="postgres_tcp", required=False)
    service = _service(check)
    body = service.liveness()
    assert body.status == "healthy"
    assert check.calls == 0
    assert body.service == "bergama-api-test"


@pytest.mark.asyncio
async def test_startup_503_before_started() -> None:
    runtime = RuntimeState()
    service = HealthService(
        settings=_settings(),
        clock=FixedClock(datetime(2026, 7, 12, tzinfo=UTC)),
        runtime_state=runtime,
        checks=(),
    )
    body, code = service.startup()
    assert code == 503
    assert body.status == "starting"


@pytest.mark.asyncio
async def test_startup_200_after_started() -> None:
    service = _service()
    body, code = service.startup()
    assert code == 200
    assert body.status == "started"


@pytest.mark.asyncio
async def test_required_pass_ready() -> None:
    service = _service(
        FakeCheck(name="a", required=True),
        FakeCheck(name="b", required=False),
    )
    body, code = await service.readiness()
    assert code == 200
    assert body.status == "ready"
    assert [c.name for c in body.checks] == ["a", "b"]


@pytest.mark.asyncio
async def test_optional_fail_degraded_200() -> None:
    service = _service(
        FakeCheck(name="req", required=True),
        FakeCheck(name="opt", required=False, status=DependencyHealthStatus.FAIL),
    )
    body, code = await service.readiness()
    assert code == 200
    assert body.status == "degraded"


@pytest.mark.asyncio
async def test_required_fail_not_ready_503() -> None:
    service = _service(
        FakeCheck(name="req", required=True, status=DependencyHealthStatus.FAIL),
        FakeCheck(name="opt", required=False),
    )
    body, code = await service.readiness()
    assert code == 503
    assert body.status == "not_ready"


@pytest.mark.asyncio
async def test_timeout_produces_timeout_result() -> None:
    service = _service(FakeCheck(name="slow", required=True, hang=True, timeout_seconds=0.05))
    body, code = await service.readiness()
    assert code == 503
    assert body.checks[0].status is DependencyHealthStatus.TIMEOUT
    assert body.checks[0].error_code == ERROR_CHECK_TIMEOUT
    assert "timed out" in (body.checks[0].message or "")


@pytest.mark.asyncio
async def test_one_exception_does_not_cancel_others() -> None:
    boom = FakeCheck(name="boom", required=False, raise_exc=RuntimeError("boom-secret-xyz"))
    ok = FakeCheck(name="ok", required=False)
    service = _service(boom, ok)
    body, code = await service.readiness()
    assert code == 200
    assert body.status == "degraded"
    assert body.checks[0].status is DependencyHealthStatus.FAIL
    assert body.checks[1].status is DependencyHealthStatus.PASS
    payload = body.model_dump_json()
    assert "boom-secret-xyz" not in payload


@pytest.mark.asyncio
async def test_result_order_is_deterministic() -> None:
    slow = FakeCheck(name="z_slow", required=False, hang=True, timeout_seconds=0.05)
    fast = FakeCheck(name="a_fast", required=False)
    service = _service(slow, fast)
    body, _ = await service.readiness()
    assert [c.name for c in body.checks] == ["z_slow", "a_fast"]


@pytest.mark.asyncio
async def test_latency_is_measured() -> None:
    service = _service(FakeCheck(name="x", required=False))
    body, _ = await service.readiness()
    assert body.checks[0].latency_ms >= 0


def test_negative_timeout_configuration_fails() -> None:
    with pytest.raises(ValidationError):
        _settings(health_check_timeout_seconds=-1)


def test_zero_timeout_configuration_fails() -> None:
    with pytest.raises(ValidationError):
        _settings(health_check_timeout_seconds=0)


def test_health_service_is_container_owned() -> None:
    container = build_container(_settings())
    assert isinstance(container.health_service, HealthService)
    other = build_container(_settings())
    assert container.health_service is not other.health_service
    assert container.runtime_state is not other.runtime_state


def test_two_containers_have_isolated_runtime_state() -> None:
    c1 = build_container(_settings())
    c2 = build_container(_settings())
    c1.runtime_state.mark_started()
    assert c1.runtime_state.state.value == "started"
    assert c2.runtime_state.state.value == "initializing"


@pytest.mark.asyncio
async def test_no_raw_exception_or_secrets_in_response() -> None:
    secret = "super-secret-connection-string"
    service = _service(
        FakeCheck(name="db", required=True, raise_exc=RuntimeError(secret)),
    )
    body, _ = await service.readiness()
    dumped = body.model_dump_json()
    assert secret not in dumped
    assert "Traceback" not in dumped
    assert body.checks[0].message == "dependency unavailable"


@pytest.mark.asyncio
async def test_legacy_aliases_use_same_service_methods() -> None:
    service = _service(FakeCheck(name="x", required=False))
    live = service.liveness()
    ready, code = await service.readiness()
    assert live.status == "healthy"
    assert code == 200
    assert ready.status == "ready"


def test_no_request_context_stored_on_health_service() -> None:
    service = _service()
    token = set_log_context(LogContext(request_id="req-1", correlation_id="corr-1"))
    try:
        body = service.liveness()
        assert body.request_id == "req-1"
    finally:
        reset_log_context(token)
    assert not hasattr(service, "request_id")
    assert "req-1" not in repr(service.__dict__)
