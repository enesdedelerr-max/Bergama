"""Integration tests for health runtime endpoints."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field

import pytest
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.factory import create_app
from app.schemas.health import DependencyHealthResult, DependencyHealthStatus
from httpx import ASGITransport, AsyncClient


@dataclass(slots=True)
class FakeCheck:
    name: str
    required: bool
    timeout_seconds: float = 1.0
    status: DependencyHealthStatus = DependencyHealthStatus.PASS
    message: str | None = "ok"
    calls: int = field(default=0, init=False)

    async def check(self) -> DependencyHealthResult:
        self.calls += 1
        return DependencyHealthResult(
            name=self.name,
            status=self.status,
            required=self.required,
            latency_ms=0.5,
            message=self.message,
        )


def _settings(**overrides: object) -> AppSettings:
    base: dict[str, object] = {
        "app_name": "bergama-api-test",
        "app_version": "0.2.0",
        "environment": AppEnvironment.TEST,
        "debug": False,
        "docs_enabled": True,
        "openapi_enabled": True,
        "log_level": "WARNING",
        "api_prefix": "/api/v1",
        "service_name": "bergama-api-test",
        "instance_id": "test-1",
        "bootstrap_auth_enabled": False,
    }
    base.update(overrides)
    return AppSettings(**base)  # type: ignore[arg-type]


@pytest.fixture
async def live_client() -> AsyncIterator[AsyncClient]:
    application = create_app(_settings())
    async with application.router.lifespan_context(application):
        transport = ASGITransport(app=application)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest.mark.asyncio
async def test_health_live_returns_200(live_client: AsyncClient) -> None:
    response = await live_client.get("/health/live")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "bergama-api-test"
    assert "request_id" in body


@pytest.mark.asyncio
async def test_health_startup_returns_200_after_lifespan(live_client: AsyncClient) -> None:
    response = await live_client.get("/health/startup")
    assert response.status_code == 200
    assert response.json()["status"] == "started"


@pytest.mark.asyncio
async def test_health_ready_default_skipped_optional_is_ready(live_client: AsyncClient) -> None:
    response = await live_client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert [c["name"] for c in body["checks"]] == ["postgres_tcp", "redis_tcp", "kafka"]
    assert all(c["status"] == "skipped" for c in body["checks"])


@pytest.mark.asyncio
async def test_health_alias_returns_200(live_client: AsyncClient) -> None:
    response = await live_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_ready_alias_follows_readiness(live_client: AsyncClient) -> None:
    response = await live_client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_cache_control_no_store(live_client: AsyncClient) -> None:
    for path in ("/health/live", "/health/ready", "/health/startup", "/health", "/ready"):
        response = await live_client.get(path)
        assert response.headers.get("cache-control") == "no-store"


@pytest.mark.asyncio
async def test_response_includes_request_id(live_client: AsyncClient) -> None:
    response = await live_client.get("/health/live", headers={"X-Request-ID": "probe-req-1"})
    assert response.json()["request_id"] == "probe-req-1"
    assert response.headers.get("x-request-id") == "probe-req-1"


@pytest.mark.asyncio
async def test_required_failure_produces_503() -> None:
    settings = _settings()
    checks = (
        FakeCheck(name="req", required=True, status=DependencyHealthStatus.FAIL),
        FakeCheck(name="opt", required=False),
    )
    container = build_container(settings, health_checks=checks)
    application = create_app(container=container)
    async with application.router.lifespan_context(application):
        transport = ASGITransport(app=application)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"


@pytest.mark.asyncio
async def test_optional_failure_produces_degraded_200() -> None:
    settings = _settings()
    checks = (
        FakeCheck(name="req", required=True),
        FakeCheck(name="opt", required=False, status=DependencyHealthStatus.FAIL),
    )
    container = build_container(settings, health_checks=checks)
    application = create_app(container=container)
    async with application.router.lifespan_context(application):
        transport = ASGITransport(app=application)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"


@pytest.mark.asyncio
async def test_concurrent_checks_do_not_leak_state_between_requests() -> None:
    settings = _settings()
    check = FakeCheck(name="shared", required=False)
    container = build_container(settings, health_checks=(check,))
    application = create_app(container=container)
    async with application.router.lifespan_context(application):
        transport = ASGITransport(app=application)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get("/health/ready")
            second = await client.get("/health/ready")
    assert first.status_code == 200
    assert second.status_code == 200
    assert check.calls == 2


@pytest.mark.asyncio
async def test_openapi_includes_new_health_paths(live_client: AsyncClient) -> None:
    document = (await live_client.get("/openapi.json")).json()
    paths = document["paths"]
    assert "/health/live" in paths
    assert "/health/ready" in paths
    assert "/health/startup" in paths
    assert "/health" in paths
    assert "/ready" in paths


@pytest.mark.asyncio
async def test_no_secret_values_in_health_output(live_client: AsyncClient) -> None:
    response = await live_client.get("/health/ready")
    text = response.text.lower()
    assert "password" not in text
    assert "secret" not in text
    assert "bootstrap" not in text
