"""Unit tests for AppContainer construction and ownership."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import pytest
from app.core.clock import FixedClock, FixedJtiGenerator, SystemClock, UuidJtiGenerator
from app.core.config import AppSettings
from app.core.container import AppContainer, build_container
from app.core.environment import AppEnvironment
from app.core.secrets import SecretSettings
from app.deps.container import get_app_container
from app.factory import create_app
from app.health.runtime_state import RuntimeState
from app.health.service import HealthService
from app.services.token_service import TokenService
from fastapi import FastAPI, Request
from starlette.requests import Request as StarletteRequest
from tests.conftest import VALID_PROD_JWT_SECRET


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
        "bootstrap_auth_enabled": True,
        "jwt_issuer": "bergama-api",
        "jwt_audience": "bergama-api",
        "jwt_access_token_ttl_seconds": 900,
        "secrets": SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
    }
    base.update(overrides)
    return AppSettings(**base)  # type: ignore[arg-type]


def test_build_container_creates_all_current_dependencies() -> None:
    settings = _settings()
    container = build_container(settings)
    assert isinstance(container, AppContainer)
    assert container.settings is settings
    assert isinstance(container.clock, SystemClock)
    assert isinstance(container.jti_generator, UuidJtiGenerator)
    assert isinstance(container.token_service, TokenService)
    assert isinstance(container.runtime_state, RuntimeState)
    assert isinstance(container.health_service, HealthService)


def test_container_holds_same_settings_instance() -> None:
    settings = _settings()
    container = build_container(settings)
    assert container.settings is settings


def test_token_service_uses_container_clock_and_jti() -> None:
    settings = _settings()
    clock = FixedClock(datetime.now(UTC).replace(microsecond=0))
    jti = FixedJtiGenerator("fixed-jti-container-1")
    container = build_container(settings, clock=clock, jti_generator=jti)
    token = container.token_service.create_bootstrap_access_token()
    claims = container.token_service.decode_access_token(token.access_token)
    assert claims.jti == "fixed-jti-container-1"
    assert claims.iat == int(clock.now().timestamp())
    assert container.clock is clock
    assert container.jti_generator is jti


def test_create_app_accepts_explicit_container() -> None:
    settings = _settings()
    container = build_container(settings)
    app = create_app(container=container)
    assert app.state.container is container


def test_create_app_does_not_rebuild_supplied_container() -> None:
    settings = _settings()
    container = build_container(settings)
    app = create_app(settings=settings, container=container)
    assert app.state.container is container
    assert app.state.container.token_service is container.token_service


def test_settings_container_mismatch_fails() -> None:
    settings_a = _settings(instance_id="a")
    settings_b = _settings(instance_id="b")
    container = build_container(settings_a)
    with pytest.raises(ValueError, match="same instance"):
        create_app(settings=settings_b, container=container)


def test_get_app_container_returns_typed_container() -> None:
    settings = _settings()
    container = build_container(settings)
    app = create_app(container=container)
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
        "app": app,
    }
    request = StarletteRequest(scope)
    resolved = get_app_container(request)
    assert resolved is container
    assert isinstance(resolved, AppContainer)


def test_missing_container_fails_clearly() -> None:
    app = FastAPI()
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
        "app": app,
    }
    request = Request(scope)
    with pytest.raises(RuntimeError, match="application container is not configured"):
        get_app_container(request)


def test_two_containers_are_isolated() -> None:
    c1 = build_container(_settings(instance_id="one"))
    c2 = build_container(_settings(instance_id="two"))
    assert c1 is not c2
    assert c1.token_service is not c2.token_service
    assert c1.settings.instance_id == "one"
    assert c2.settings.instance_id == "two"


def test_no_global_state_leaks_across_containers() -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    clock1 = FixedClock(now - timedelta(seconds=60))
    clock2 = FixedClock(now - timedelta(seconds=30))
    c1 = build_container(_settings(), clock=clock1, jti_generator=FixedJtiGenerator("a"))
    c2 = build_container(_settings(), clock=clock2, jti_generator=FixedJtiGenerator("b"))
    t1 = c1.token_service.create_bootstrap_access_token()
    t2 = c2.token_service.create_bootstrap_access_token()
    claims1 = c1.token_service.decode_access_token(t1.access_token)
    claims2 = c2.token_service.decode_access_token(t2.access_token)
    assert claims1.jti == "a"
    assert claims2.jti == "b"
    assert claims1.iat != claims2.iat


@pytest.mark.asyncio
async def test_cleanup_is_idempotent() -> None:
    container = build_container(_settings())
    await container.aclose()
    await container.aclose()
    assert container._closed is True


@pytest.mark.asyncio
async def test_cleanup_failure_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    container = build_container(_settings())

    async def _boom() -> None:
        raise RuntimeError("cleanup boom")

    container._exit_stack.push_async_callback(_boom)
    with caplog.at_level(logging.ERROR), pytest.raises(RuntimeError, match="cleanup boom"):
        await container.aclose()
    assert any("container cleanup failed" in r.message for r in caplog.records)


def test_no_request_scoped_context_stored_in_container() -> None:
    build_container(_settings())
    field_names = set(AppContainer.__dataclass_fields__)
    forbidden = {
        "request_id",
        "correlation_id",
        "causation_id",
        "principal",
        "authenticated_principal",
        "request",
    }
    assert field_names.isdisjoint(forbidden)


def test_auth_config_unchanged_on_container_settings() -> None:
    settings = _settings(
        jwt_algorithm="HS256",
        jwt_issuer="bergama-api",
        jwt_audience="bergama-api",
        jwt_access_token_ttl_seconds=900,
        bootstrap_auth_enabled=True,
    )
    container = build_container(settings)
    assert container.settings.jwt_algorithm == "HS256"
    assert container.settings.jwt_issuer == "bergama-api"
    assert container.settings.jwt_audience == "bergama-api"
    assert container.settings.jwt_access_token_ttl_seconds == 900
    assert container.settings.bootstrap_auth_enabled is True
