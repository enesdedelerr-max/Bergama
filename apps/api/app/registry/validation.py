"""Registry schema/version and shallow dependency validation."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from app.registry.errors import (
    RegistryDependencyCycleError,
    RegistryDependencyMissingError,
    RegistryMissingRequiredError,
    RegistrySchemaInvalidError,
    RegistrySelfDependencyError,
    RegistryUnsupportedSchemaVersionError,
)
from app.registry.models import LoadedRegistry, RegistryDocument, schema_major, validate_semver

_EXACT_CONSTRAINT = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
_RANGE_CONSTRAINT = re.compile(
    r"^>=\s*(?P<lower>\d+\.\d+\.\d+)\s*,\s*<\s*(?P<upper>\d+\.\d+\.\d+)$"
)


def validate_document_mapping(
    data: Mapping[str, object],
    *,
    supported_schema_major: int,
) -> RegistryDocument:
    """Validate root mapping into RegistryDocument; enforce schema major policy.

    Compatibility rule: loader supports configured schema major only.
    Minor/patch of schema_version are accepted when the document shape validates.
    Other majors fail closed with registry.unsupported_schema_version.
    """
    try:
        document = RegistryDocument.model_validate(dict(data))
    except ValueError as exc:
        message = str(exc)
        if "self-dependency" in message:
            raise RegistrySelfDependencyError(message) from exc
        raise RegistrySchemaInvalidError("registry schema invalid") from exc
    except Exception as exc:
        raise RegistrySchemaInvalidError("registry schema invalid") from exc

    major = schema_major(document.registry.schema_version)
    if major != supported_schema_major:
        raise RegistryUnsupportedSchemaVersionError(
            f"unsupported schema major {major}; expected {supported_schema_major}"
        )
    # Document version must also be valid semver (already enforced on model).
    validate_semver(document.registry.version)
    return document


def validate_required_ids(
    loaded: Sequence[LoadedRegistry],
    required_ids: Sequence[str],
) -> None:
    present = {item.registry_id for item in loaded}
    missing = sorted(rid for rid in required_ids if rid not in present)
    if missing:
        raise RegistryMissingRequiredError(f"missing required registry ids: {', '.join(missing)}")


def validate_shallow_dependencies(loaded: Sequence[LoadedRegistry]) -> None:
    """Validate self-deps (already on model), required presence, and cycles."""
    by_id = {item.registry_id: item for item in loaded}
    # Deterministic error order by registry_id then dependency order.
    for item in sorted(loaded, key=lambda entry: entry.registry_id):
        for dep in item.document.registry.dependencies:
            if dep.registry_id == item.registry_id:
                raise RegistrySelfDependencyError(f"self-dependency on {dep.registry_id!r}")
            target = by_id.get(dep.registry_id)
            if target is None:
                if dep.required:
                    raise RegistryDependencyMissingError(
                        f"missing required dependency {dep.registry_id!r} "
                        f"for registry {item.registry_id!r}"
                    )
                continue
            if (
                not _constraint_matches(target.document.registry.version, dep.version_constraint)
                and dep.required
            ):
                raise RegistryDependencyMissingError(
                    f"dependency {dep.registry_id!r} version "
                    f"{target.document.registry.version!r} does not satisfy "
                    f"{dep.version_constraint!r} for registry {item.registry_id!r}"
                )
    _detect_cycles(loaded)


def _constraint_matches(version: str, constraint: str) -> bool:
    text = constraint.strip()
    if text in {"*", ">=0.0.0"}:
        return True
    if _EXACT_CONSTRAINT.fullmatch(text):
        return version == text
    match = _RANGE_CONSTRAINT.fullmatch(text)
    if match is not None:
        lower = match.group("lower")
        upper = match.group("upper")
        return _semver_tuple(version) >= _semver_tuple(lower) and _semver_tuple(
            version
        ) < _semver_tuple(upper)
    # Compatible-major shorthand: ^1.0.0 → same major, >= 1.0.0
    if text.startswith("^"):
        base = text[1:].strip()
        if _EXACT_CONSTRAINT.fullmatch(base):
            major, _, _ = base.partition(".")
            v_major, _, _ = version.partition(".")
            return v_major == major and _semver_tuple(version) >= _semver_tuple(base)
    # Unsupported constraint forms fail closed for required deps (caller treats as mismatch).
    return False


def _semver_tuple(version: str) -> tuple[int, int, int]:
    core = version.split("-", 1)[0].split("+", 1)[0]
    major_s, minor_s, patch_s = core.split(".", 2)
    return int(major_s), int(minor_s), int(patch_s)


def _detect_cycles(loaded: Sequence[LoadedRegistry]) -> None:
    graph = {
        item.registry_id: [dep.registry_id for dep in item.document.registry.dependencies]
        for item in loaded
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str, stack: list[str]) -> None:
        if node in visited:
            return
        if node in visiting:
            cycle = " -> ".join([*stack[stack.index(node) :], node])
            raise RegistryDependencyCycleError(f"dependency cycle detected: {cycle}")
        visiting.add(node)
        for nxt in graph.get(node, []):
            if nxt in graph:
                dfs(nxt, [*stack, node])
        visiting.remove(node)
        visited.add(node)

    for registry_id in sorted(graph):
        dfs(registry_id, [])
