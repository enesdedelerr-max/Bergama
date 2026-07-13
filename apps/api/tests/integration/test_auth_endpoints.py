"""Integration tests for JWT bootstrap auth endpoints."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import jwt
import pytest
from app.core.clock import FixedClock
from app.core.config import AppSettings
from app.core.environment import AppEnvironment
from app.core.logging import configure_logging
from app.core.secrets import SecretSettings
from app.core.security import BOOTSTRAP_SUBJECT, TOKEN_TYPE_ACCESS
from app.factory import create_app
from app.services.token_service import TokenService
from httpx import ASGITransport, AsyncClient
from tests.conftest import VALID_PROD_JWT_SECRET


def _local_auth_settings() -> AppSettings:
    return AppSettings(
        environment=AppEnvironment.LOCAL,
        debug=True,
        docs_enabled=True,
        openapi_enabled=True,
        log_level="INFO",
        bootstrap_auth_enabled=True,
        jwt_access_token_ttl_seconds=900,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
    )


@pytest.fixture
async def local_auth_client() -> AsyncIterator[AsyncClient]:
    application = create_app(_local_auth_settings())
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_local_token_endpoint_issues_bearer_token(local_auth_client: AsyncClient) -> None:
    response = await local_auth_client.post(
        "/api/v1/auth/token",
        json={"grant_type": "bootstrap"},
    )
    assert response.status_code == 200
    assert response.headers.get("cache-control") == "no-store"
    assert response.headers.get("pragma") == "no-cache"
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 900
    assert isinstance(body["access_token"], str)
    assert body["access_token"]
    assert VALID_PROD_JWT_SECRET not in body["access_token"]


@pytest.mark.asyncio
async def test_auth_me_with_valid_token(local_auth_client: AsyncClient) -> None:
    token = (
        await local_auth_client.post("/api/v1/auth/token", json={"grant_type": "bootstrap"})
    ).json()["access_token"]
    response = await local_auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "subject": BOOTSTRAP_SUBJECT,
        "roles": ["developer"],
        "scopes": ["api:read"],
    }


@pytest.mark.asyncio
async def test_auth_me_missing_token_returns_401(local_auth_client: AsyncClient) -> None:
    response = await local_auth_client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.headers.get("www-authenticate") == "Bearer"
    assert response.json()["code"] == "auth.missing_token"


@pytest.mark.asyncio
async def test_auth_me_malformed_and_invalid_token_return_401(
    local_auth_client: AsyncClient,
) -> None:
    malformed = await local_auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Token nope"},
    )
    assert malformed.status_code == 401

    invalid = await local_auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert invalid.status_code == 401
    assert invalid.headers.get("www-authenticate") == "Bearer"
    assert invalid.json()["code"] == "auth.invalid_token"


@pytest.mark.asyncio
async def test_auth_me_expired_and_wrong_audience_return_401(
    local_auth_client: AsyncClient,
) -> None:
    settings = _local_auth_settings()
    expired_service = TokenService(
        settings,
        clock=FixedClock(datetime(2020, 1, 1, tzinfo=UTC)),
        jti_factory=lambda: "jti-old",
    )
    # TTL 900s from 2020 → long expired relative to real validation clock
    expired = expired_service.create_bootstrap_access_token().access_token
    response = await local_auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired}"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "auth.expired_token"

    wrong_aud = jwt.encode(
        {
            "sub": BOOTSTRAP_SUBJECT,
            "iss": settings.jwt_issuer,
            "aud": "not-bergama",
            "iat": 1_700_000_000,
            "nbf": 1_700_000_000,
            "exp": 1_900_000_000,
            "jti": "jti-aud",
            "token_type": TOKEN_TYPE_ACCESS,
            "roles": ["developer"],
            "scopes": ["api:read"],
        },
        VALID_PROD_JWT_SECRET,
        algorithm="HS256",
    )
    aud_resp = await local_auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {wrong_aud}"},
    )
    assert aud_resp.status_code == 401
    assert aud_resp.json()["code"] == "auth.invalid_audience"


@pytest.mark.asyncio
async def test_staging_and_production_token_endpoint_disabled() -> None:
    for env in (AppEnvironment.STAGING, AppEnvironment.PRODUCTION):
        settings = AppSettings(environment=env, debug=False, bootstrap_auth_enabled=False)
        application = create_app(settings)
        transport = ASGITransport(app=application)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/token",
                json={"grant_type": "bootstrap"},
            )
            assert response.status_code == 404
            assert response.json()["code"] == "auth.bootstrap_disabled"
            assert (await client.get("/health")).status_code == 200
            assert (await client.get("/ready")).status_code == 200


@pytest.mark.asyncio
async def test_production_starts_without_bootstrap_key() -> None:
    settings = AppSettings(
        environment=AppEnvironment.PRODUCTION,
        debug=False,
        bootstrap_auth_enabled=False,
    )
    application = create_app(settings)
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get("/health")).status_code == 200


@pytest.mark.asyncio
async def test_openapi_bearer_and_no_secrets(
    local_auth_client: AsyncClient,
) -> None:
    response = await local_auth_client.get("/openapi.json")
    assert response.status_code == 200
    document = response.json()
    blob = json.dumps(document)
    assert VALID_PROD_JWT_SECRET not in blob
    assert "HTTPBearer" in document["components"]["securitySchemes"]
    me_path = document["paths"]["/api/v1/auth/me"]["get"]
    assert (
        "security" in me_path
        or any("HTTPBearer" in str(param) for param in me_path.get("parameters", []))
        or "HTTPBearer" in blob
    )


@pytest.mark.asyncio
async def test_logs_do_not_contain_raw_jwt(
    capsys: pytest.CaptureFixture[str],
) -> None:
    settings = _local_auth_settings()
    configure_logging(settings)
    application = create_app(settings)
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token_resp = await client.post("/api/v1/auth/token", json={"grant_type": "bootstrap"})
        token = token_resp.json()["access_token"]
        await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    out = capsys.readouterr().out
    assert token not in out
    assert VALID_PROD_JWT_SECRET not in out
