"""Safe YAML and JSON registry file parsers."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Literal

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode

from app.registry.errors import (
    RegistryDuplicateKeyError,
    RegistryInvalidRootError,
    RegistryParseFailedError,
)


class _UniqueKeySafeLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate mapping keys."""


def _construct_mapping_unique(
    loader: yaml.SafeLoader,
    node: MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise RegistryDuplicateKeyError(
                "duplicate key in YAML mapping",
                path=getattr(loader, "_bergama_source_path", None),
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping_unique,
)


def load_registry_mapping(
    path: Path,
    *,
    source_format: Literal["yaml", "json"],
    max_file_size_bytes: int,
) -> dict[str, Any]:
    """Parse a registry file into a root mapping. Never logs/returns file body."""
    size = path.stat().st_size
    if size > max_file_size_bytes:
        from app.registry.errors import RegistryFileTooLargeError

        raise RegistryFileTooLargeError(
            f"registry file exceeds max size ({max_file_size_bytes} bytes)",
            path=str(path),
        )
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RegistryParseFailedError("registry file is not valid UTF-8", path=str(path)) from exc

    if source_format == "json":
        return _parse_json(text, path=path)
    return _parse_yaml(text, path=path)


def _parse_json(text: str, *, path: Path) -> dict[str, Any]:
    def _pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        mapping: dict[str, Any] = {}
        for key, value in pairs:
            if key in mapping:
                raise RegistryDuplicateKeyError("duplicate key in JSON object", path=str(path))
            mapping[key] = value
        return mapping

    decoder = json.JSONDecoder(object_pairs_hook=_pairs_hook, parse_constant=_reject_json_constant)
    try:
        data, index = decoder.raw_decode(text.lstrip())
    except RegistryDuplicateKeyError:
        raise
    except json.JSONDecodeError as exc:
        raise RegistryParseFailedError("JSON parse failed", path=str(path)) from exc
    # Reconstruct trailing check against original text end after the decoded document.
    # raw_decode index is relative to the lstripped string; map back for trailing check.
    stripped = text.lstrip()
    trailing = stripped[index:].strip()
    if trailing:
        raise RegistryParseFailedError("JSON trailing garbage", path=str(path))
    if not isinstance(data, dict):
        raise RegistryInvalidRootError("registry root must be a JSON object", path=str(path))
    _reject_non_finite(data, path=path)
    return data


def _reject_json_constant(value: str) -> float:
    # json.parse_constant receives NaN / Infinity / -Infinity when allow_nan path used;
    # with default decoder these are not emitted, but keep fail-closed.
    raise RegistryParseFailedError(f"unsupported JSON constant {value!r}")


def _parse_yaml(text: str, *, path: Path) -> dict[str, Any]:
    loader = _UniqueKeySafeLoader(text)
    loader._bergama_source_path = str(path)  # type: ignore[attr-defined]
    try:
        try:
            data = loader.get_single_data()
        except RegistryDuplicateKeyError:
            raise
        except ConstructorError as exc:
            if "duplicate key" in str(exc).lower():
                raise RegistryDuplicateKeyError(
                    "duplicate key in YAML mapping",
                    path=str(path),
                ) from exc
            raise RegistryParseFailedError("YAML parse failed", path=str(path)) from exc
        except yaml.YAMLError as exc:
            raise RegistryParseFailedError("YAML parse failed", path=str(path)) from exc
    finally:
        dispose = getattr(loader, "dispose", None)
        if callable(dispose):
            dispose()

    if data is None:
        raise RegistryInvalidRootError("registry root must be a mapping", path=str(path))
    if not isinstance(data, dict):
        raise RegistryInvalidRootError("registry root must be a mapping", path=str(path))
    _reject_non_finite(data, path=path)
    return data


def _reject_non_finite(value: Any, *, path: Path) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _reject_non_finite(item, path=path)
        return
    if isinstance(value, list):
        for item in value:
            _reject_non_finite(item, path=path)
        return
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        raise RegistryParseFailedError("NaN/Infinity are not allowed", path=str(path))
