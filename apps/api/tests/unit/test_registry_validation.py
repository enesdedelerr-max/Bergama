"""Unit tests for registry validation and service behavior."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from app.core.clock import FixedClock
from app.core.registry_settings import RegistrySettings
from app.registry.errors import (
    RegistryDependencyCycleError,
    RegistryDependencyMissingError,
    RegistryDuplicateIdError,
    RegistryMissingRequiredError,
    RegistryNotFoundError,
    RegistryNotLoadedError,
)
from app.registry.service import RegistryService


def _write_registry(
    path: Path,
    *,
    registry_id: str,
    deps: list[dict[str, object]] | None = None,
    payload: dict[str, object] | None = None,
) -> None:
    document = {
        "registry": {
            "id": registry_id,
            "type": "generic",
            "version": "1.0.0",
            "schema_version": "1.0.0",
            "owner": "platform",
            "created_at": "2026-01-01T00:00:00Z",
            "dependencies": deps or [],
            "metadata": {},
        },
        "payload": payload or {"ok": True},
    }
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


@pytest.mark.asyncio
async def test_required_registry_missing_fails(tmp_path: Path) -> None:
    _write_registry(tmp_path / "a.yaml", registry_id="present-only")
    service = RegistryService(
        RegistrySettings(
            enabled=True,
            paths=[str(tmp_path)],
            required_registry_ids=["missing-required"],
        )
    )
    with pytest.raises(RegistryMissingRequiredError):
        await service.load()


@pytest.mark.asyncio
async def test_duplicate_registry_id_fails(tmp_path: Path) -> None:
    _write_registry(tmp_path / "a.yaml", registry_id="same-id")
    _write_registry(tmp_path / "b.yaml", registry_id="same-id")
    service = RegistryService(RegistrySettings(enabled=True, paths=[str(tmp_path)]))
    with pytest.raises(RegistryDuplicateIdError):
        await service.load()


@pytest.mark.asyncio
async def test_optional_dependency_missing_allowed(tmp_path: Path) -> None:
    _write_registry(
        tmp_path / "a.yaml",
        registry_id="with-optional-dep",
        deps=[
            {
                "registry_id": "absent-optional",
                "version_constraint": "*",
                "required": False,
            }
        ],
    )
    service = RegistryService(RegistrySettings(enabled=True, paths=[str(tmp_path)]))
    report = await service.load()
    assert report.registries[0].registry_id == "with-optional-dep"


@pytest.mark.asyncio
async def test_required_dependency_missing_fails(tmp_path: Path) -> None:
    _write_registry(
        tmp_path / "a.yaml",
        registry_id="with-required-dep",
        deps=[
            {
                "registry_id": "absent-required",
                "version_constraint": "*",
                "required": True,
            }
        ],
    )
    service = RegistryService(RegistrySettings(enabled=True, paths=[str(tmp_path)]))
    with pytest.raises(RegistryDependencyMissingError):
        await service.load()


@pytest.mark.asyncio
async def test_dependency_cycle_fails(tmp_path: Path) -> None:
    _write_registry(
        tmp_path / "a.yaml",
        registry_id="reg-a",
        deps=[{"registry_id": "reg-b", "version_constraint": "*", "required": True}],
    )
    _write_registry(
        tmp_path / "b.yaml",
        registry_id="reg-b",
        deps=[{"registry_id": "reg-a", "version_constraint": "*", "required": True}],
    )
    service = RegistryService(RegistrySettings(enabled=True, paths=[str(tmp_path)]))
    with pytest.raises(RegistryDependencyCycleError):
        await service.load()


@pytest.mark.asyncio
async def test_loaded_timestamp_uses_injected_clock(tmp_path: Path) -> None:
    _write_registry(tmp_path / "a.yaml", registry_id="clocked")
    instant = datetime(2026, 7, 12, 15, 30, tzinfo=UTC)
    service = RegistryService(
        RegistrySettings(enabled=True, paths=[str(tmp_path)]),
        clock=FixedClock(instant),
    )
    await service.load()
    assert service.get("clocked").loaded_at == instant


@pytest.mark.asyncio
async def test_service_lookup_and_list_order(tmp_path: Path) -> None:
    _write_registry(tmp_path / "b.yaml", registry_id="bravo")
    _write_registry(tmp_path / "a.yaml", registry_id="alpha")
    service = RegistryService(RegistrySettings(enabled=True, paths=[str(tmp_path)]))
    await service.load()
    assert [item.registry_id for item in service.list()] == ["alpha", "bravo"]
    assert service.get("alpha").registry_id == "alpha"
    with pytest.raises(RegistryNotFoundError):
        service.get("missing")


@pytest.mark.asyncio
async def test_unknown_lookup_before_load_fails(tmp_path: Path) -> None:
    service = RegistryService(RegistrySettings(enabled=True, paths=[str(tmp_path)]))
    with pytest.raises(RegistryNotLoadedError):
        service.get("x")


@pytest.mark.asyncio
async def test_disabled_registry_creates_no_loader_activity() -> None:
    service = RegistryService(RegistrySettings(enabled=False, paths=[]))
    report = await service.load()
    assert report.registries == ()
    assert service.safe_summary().count == 0
