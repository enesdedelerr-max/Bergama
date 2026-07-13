"""Integration tests for registry service + app lifecycle."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.core.registry_settings import RegistrySettings
from app.factory import create_app
from app.registry.errors import (
    RegistryInvalidRootError,
    RegistryMissingRequiredError,
    RegistrySchemaInvalidError,
)
from httpx import ASGITransport, AsyncClient


def _write_valid(path: Path, registry_id: str = "market-data-topics") -> None:
    document = {
        "registry": {
            "id": registry_id,
            "type": "topic",
            "version": "1.0.0",
            "schema_version": "1.0.0",
            "owner": "platform",
            "created_at": "2026-01-01T00:00:00Z",
            "dependencies": [],
            "metadata": {},
        },
        "payload": {"topics": ["events"]},
    }
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


@pytest.mark.asyncio
async def test_app_starts_with_registry_disabled() -> None:
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=False,
        registry=RegistrySettings(enabled=False),
    )
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            live = await client.get("/health/live")
            ready = await client.get("/health/ready")
            startup = await client.get("/health/startup")
            assert live.status_code == 200
            assert startup.status_code == 200
            assert ready.status_code == 200
            registry = next(c for c in ready.json()["checks"] if c["name"] == "registry")
            assert registry["status"] == "skipped"


@pytest.mark.asyncio
async def test_app_starts_with_valid_registry_directory(tmp_path: Path) -> None:
    _write_valid(tmp_path / "topics.yaml")
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=False,
        registry=RegistrySettings(
            enabled=True,
            paths=[str(tmp_path)],
            required_registry_ids=["market-data-topics"],
            load_on_startup=True,
        ),
    )
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            assert (await client.get("/health/live")).status_code == 200
            assert (await client.get("/health/startup")).status_code == 200
            ready = await client.get("/health/ready")
            assert ready.status_code == 200
            registry = next(c for c in ready.json()["checks"] if c["name"] == "registry")
            assert registry["status"] == "pass"
            body_text = ready.text
            assert "payload" not in body_text
            assert "source_path" not in body_text
            assert "topics" not in body_text


@pytest.mark.asyncio
async def test_app_startup_fails_for_missing_required_registry(tmp_path: Path) -> None:
    _write_valid(tmp_path / "topics.yaml", registry_id="other-id")
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=False,
        registry=RegistrySettings(
            enabled=True,
            paths=[str(tmp_path)],
            required_registry_ids=["market-data-topics"],
            load_on_startup=True,
        ),
    )
    app = create_app(settings)
    with pytest.raises(RegistryMissingRequiredError):
        async with app.router.lifespan_context(app):
            pass


@pytest.mark.asyncio
async def test_app_startup_fails_for_invalid_discovered_registry(tmp_path: Path) -> None:
    (tmp_path / "bad.yaml").write_text("registry: []\npayload: {}\n", encoding="utf-8")
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=False,
        registry=RegistrySettings(
            enabled=True,
            paths=[str(tmp_path)],
            load_on_startup=True,
        ),
    )
    app = create_app(settings)
    with pytest.raises((RegistrySchemaInvalidError, RegistryInvalidRootError)):
        async with app.router.lifespan_context(app):
            pass


@pytest.mark.asyncio
async def test_registry_health_fail_when_enabled_but_not_loaded(tmp_path: Path) -> None:
    _write_valid(tmp_path / "topics.yaml")
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=False,
        registry=RegistrySettings(
            enabled=True,
            paths=[str(tmp_path)],
            load_on_startup=False,
            health_required=True,
        ),
    )
    container = build_container(settings)
    app = create_app(settings, container=container)
    # Do not call load — enabled but not loaded.
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ready = await client.get("/health/ready")
        assert ready.status_code == 503
        registry = next(c for c in ready.json()["checks"] if c["name"] == "registry")
        assert registry["status"] == "fail"


@pytest.mark.asyncio
async def test_separate_containers_do_not_share_registry_state(tmp_path: Path) -> None:
    _write_valid(tmp_path / "topics.yaml")
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=False,
        registry=RegistrySettings(enabled=True, paths=[str(tmp_path)]),
    )
    c1 = build_container(settings)
    c2 = build_container(settings)
    await c1.registry_service.load()
    assert c1.registry_service.is_loaded is True
    assert c2.registry_service.is_loaded is False
    assert c1.registry_service is not c2.registry_service


@pytest.mark.asyncio
async def test_auth_and_kafka_unchanged_with_registry_disabled() -> None:
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=False,
        registry=RegistrySettings(enabled=False),
    )
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            ready = await client.get("/health/ready")
            names = [c["name"] for c in ready.json()["checks"]]
            assert names == ["postgres_tcp", "redis_tcp", "kafka", "registry"]
            assert all(
                c["status"] == "skipped"
                for c in ready.json()["checks"]
                if c["name"] in {"kafka", "registry"}
            )
