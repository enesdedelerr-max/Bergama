"""CORS middleware integration tests (Sprint 15 WS1 / #168)."""

from __future__ import annotations

import pytest
from app.core.config import AppSettings
from app.core.environment import AppEnvironment
from app.factory import create_app
from httpx import ASGITransport, AsyncClient


def _settings(*, allowed_origins: str = "") -> AppSettings:
    return AppSettings(
        app_name="bergama-api-test",
        app_version="0.2.0",
        environment=AppEnvironment.TEST,
        debug=False,
        docs_enabled=False,
        openapi_enabled=False,
        log_level="WARNING",
        api_prefix="/api/v1",
        service_name="bergama-api-test",
        instance_id="test-cors",
        bootstrap_auth_enabled=False,
        cors={"allowed_origins": allowed_origins},
    )


@pytest.mark.asyncio
async def test_cors_allowlisted_origin_preflight() -> None:
    application = create_app(_settings(allowed_origins="http://localhost:3000"))
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options(
            "/health/live",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization,Content-Type",
            },
        )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") in {None, "false"}
    allow_methods = response.headers.get("access-control-allow-methods", "")
    assert "GET" in allow_methods
    assert "POST" in allow_methods
    assert "OPTIONS" in allow_methods
    allow_headers = response.headers.get("access-control-allow-headers", "").lower()
    assert "authorization" in allow_headers
    assert "content-type" in allow_headers
    assert "access-control-expose-headers" not in {
        k.lower() for k in response.headers
    } or response.headers.get("access-control-expose-headers") in {None, ""}
    assert response.headers.get("access-control-max-age") is None
    cors_middleware = next(
        m
        for m in application.user_middleware
        if getattr(m, "cls", None) is not None and m.cls.__name__ == "CORSMiddleware"
    )
    assert "max_age" not in cors_middleware.kwargs


@pytest.mark.asyncio
async def test_cors_denied_origin() -> None:
    application = create_app(_settings(allowed_origins="http://localhost:3000"))
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/health/live",
            headers={"Origin": "https://evil.example"},
        )
    assert response.headers.get("access-control-allow-origin") is None


@pytest.mark.asyncio
async def test_cors_unset_empty_denies_all() -> None:
    application = create_app(_settings(allowed_origins=""))
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/health/live",
            headers={"Origin": "http://localhost:3000"},
        )
    assert response.headers.get("access-control-allow-origin") is None


@pytest.mark.asyncio
async def test_cors_credentials_false_on_allowed_get() -> None:
    application = create_app(_settings(allowed_origins="http://localhost:3000"))
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/health/live",
            headers={"Origin": "http://localhost:3000"},
        )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    # Starlette omits the header when credentials are false.
    assert response.headers.get("access-control-allow-credentials") in {None, "false"}
