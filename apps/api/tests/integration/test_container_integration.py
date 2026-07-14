"""Integration tests for AppContainer wiring through FastAPI."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from app.core.clock import FixedClock, FixedJtiGenerator
from app.core.config import AppSettings
from app.core.container import AppContainer, build_container
from app.core.environment import AppEnvironment
from app.core.secrets import SecretSettings
from app.deps.auth import get_token_service
from app.deps.container import get_app_container
from app.factory import create_app
from app.services.token_service import TokenService
from httpx import ASGITransport, AsyncClient
from starlette.requests import Request
from tests.conftest import VALID_PROD_JWT_SECRET


def _auth_settings(**overrides: object) -> AppSettings:
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
        "bootstrap_auth_enabled": True,
        "jwt_issuer": "bergama-api",
        "jwt_audience": "bergama-api",
        "jwt_access_token_ttl_seconds": 900,
        "secrets": SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
    }
    base.update(overrides)
    return AppSettings(**base)  # type: ignore[arg-type]


@pytest.fixture
async def auto_client() -> AsyncIterator[AsyncClient]:
    application = create_app(_auth_settings())
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def fixed_container() -> AppContainer:
    settings = _auth_settings()
    clock = FixedClock(datetime.now(UTC).replace(microsecond=0))
    jti = FixedJtiGenerator("integration-fixed-jti")
    return build_container(settings, clock=clock, jti_generator=jti)


@pytest.fixture
async def fixed_client(fixed_container: AppContainer) -> AsyncIterator[AsyncClient]:
    application = create_app(container=fixed_container)
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_app_starts_with_auto_built_container(auto_client: AsyncClient) -> None:
    response = await auto_client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_app_starts_with_explicit_test_container(fixed_client: AsyncClient) -> None:
    response = await fixed_client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_returns_200(auto_client: AsyncClient) -> None:
    response = await auto_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_ready_returns_200(auto_client: AsyncClient) -> None:
    response = await auto_client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_local_token_issuance_works(auto_client: AsyncClient) -> None:
    response = await auto_client.post("/api/v1/auth/token", json={"grant_type": "bootstrap"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert "access_token" in body


@pytest.mark.asyncio
async def test_auth_me_works(auto_client: AsyncClient) -> None:
    token_response = await auto_client.post("/api/v1/auth/token", json={"grant_type": "bootstrap"})
    token = token_response.json()["access_token"]
    me = await auto_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    assert me.json()["subject"] == "local-bootstrap-user"


@pytest.mark.asyncio
async def test_auth_dependency_resolves_token_service_from_container(
    fixed_container: AppContainer,
) -> None:
    application = create_app(container=fixed_container)
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 123),
        "server": ("test", 80),
        "app": application,
    }
    request = Request(scope)
    service = get_token_service(request)
    assert service is fixed_container.token_service
    assert get_app_container(request).token_service is fixed_container.token_service
    assert isinstance(service, TokenService)


@pytest.mark.asyncio
async def test_fixed_clock_jti_produces_deterministic_claims(
    fixed_client: AsyncClient,
    fixed_container: AppContainer,
) -> None:
    response = await fixed_client.post("/api/v1/auth/token", json={"grant_type": "bootstrap"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    claims = fixed_container.token_service.decode_access_token(token)
    assert claims.jti == "integration-fixed-jti"
    assert claims.iat == int(fixed_container.clock.now().timestamp())


@pytest.mark.asyncio
async def test_separate_app_instances_do_not_share_container() -> None:
    c1 = build_container(_auth_settings(instance_id="app-1"), jti_generator=FixedJtiGenerator("j1"))
    c2 = build_container(_auth_settings(instance_id="app-2"), jti_generator=FixedJtiGenerator("j2"))
    app1 = create_app(container=c1)
    app2 = create_app(container=c2)
    assert app1.state.container is c1
    assert app2.state.container is c2
    assert app1.state.container is not app2.state.container
    assert app1.state.container.token_service is not app2.state.container.token_service


@pytest.mark.asyncio
async def test_shutdown_lifecycle_completes(fixed_container: AppContainer) -> None:
    application = create_app(container=fixed_container)
    async with application.router.lifespan_context(application):
        transport = ASGITransport(app=application)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
    assert fixed_container._closed is True
