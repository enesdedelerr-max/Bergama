"""Unit tests for YAML/JSON registry loaders."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.core.registry_settings import RegistrySettings
from app.registry.errors import (
    RegistryDuplicateKeyError,
    RegistryFileTooLargeError,
    RegistryInvalidRootError,
    RegistryParseFailedError,
    RegistryUnsupportedExtensionError,
)
from app.registry.loaders import load_registry_mapping
from app.registry.service import RegistryService


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.asyncio
async def test_valid_yaml_loads(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "a.yaml",
        """
registry:
  id: sample-a
  type: generic
  version: 1.0.0
  schema_version: 1.0.0
  owner: platform
  created_at: 2026-01-01T00:00:00Z
  dependencies: []
  metadata: {}
payload:
  x: 1
""",
    )
    mapping = load_registry_mapping(path, source_format="yaml", max_file_size_bytes=10_000)
    assert mapping["registry"]["id"] == "sample-a"


@pytest.mark.asyncio
async def test_valid_json_loads(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "a.json",
        """
{
  "registry": {
    "id": "sample-b",
    "type": "generic",
    "version": "1.0.0",
    "schema_version": "1.0.0",
    "owner": "platform",
    "created_at": "2026-01-01T00:00:00Z",
    "dependencies": [],
    "metadata": {}
  },
  "payload": {"x": 1}
}
""",
    )
    mapping = load_registry_mapping(path, source_format="json", max_file_size_bytes=10_000)
    assert mapping["registry"]["id"] == "sample-b"


def test_invalid_yaml_fails(tmp_path: Path) -> None:
    path = _write(tmp_path / "bad.yaml", "registry: [\n")
    with pytest.raises(RegistryParseFailedError):
        load_registry_mapping(path, source_format="yaml", max_file_size_bytes=10_000)


def test_invalid_json_fails(tmp_path: Path) -> None:
    path = _write(tmp_path / "bad.json", '{"registry":')
    with pytest.raises(RegistryParseFailedError):
        load_registry_mapping(path, source_format="json", max_file_size_bytes=10_000)


def test_non_object_root_fails(tmp_path: Path) -> None:
    path = _write(tmp_path / "list.json", "[1,2,3]")
    with pytest.raises(RegistryInvalidRootError):
        load_registry_mapping(path, source_format="json", max_file_size_bytes=10_000)


def test_duplicate_json_key_fails(tmp_path: Path) -> None:
    path = _write(tmp_path / "dup.json", '{"a":1,"a":2}')
    with pytest.raises(RegistryDuplicateKeyError):
        load_registry_mapping(path, source_format="json", max_file_size_bytes=10_000)


def test_duplicate_yaml_key_fails(tmp_path: Path) -> None:
    path = _write(tmp_path / "dup.yaml", "a: 1\na: 2\n")
    with pytest.raises(RegistryDuplicateKeyError):
        load_registry_mapping(path, source_format="yaml", max_file_size_bytes=10_000)


def test_oversized_file_fails(tmp_path: Path) -> None:
    path = _write(tmp_path / "big.yaml", "x: " + ("y" * 100))
    with pytest.raises(RegistryFileTooLargeError):
        load_registry_mapping(path, source_format="yaml", max_file_size_bytes=10)


def test_nan_rejected_in_json(tmp_path: Path) -> None:
    # Standard json module rejects NaN by default via allow_nan=False path;
    # force via YAML which can emit float nan.
    path = _write(tmp_path / "nan.yaml", "value: .nan\n")
    with pytest.raises(RegistryParseFailedError):
        load_registry_mapping(path, source_format="yaml", max_file_size_bytes=10_000)


@pytest.mark.asyncio
async def test_unsupported_extension_fails(tmp_path: Path) -> None:
    _write(tmp_path / "notes.txt", "hello")
    service = RegistryService(
        RegistrySettings(
            enabled=True,
            paths=[str(tmp_path)],
            fail_on_unknown_files=True,
        )
    )
    with pytest.raises(RegistryUnsupportedExtensionError):
        await service.load()


@pytest.mark.asyncio
async def test_missing_path_fails() -> None:
    service = RegistryService(
        RegistrySettings(enabled=True, paths=["/tmp/bergama-missing-registry-dir-xyz"])
    )
    from app.registry.errors import RegistryPathNotFoundError

    with pytest.raises(RegistryPathNotFoundError):
        await service.load()
