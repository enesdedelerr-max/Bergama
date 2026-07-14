"""Protocols for registry loading."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Protocol

from app.registry.models import (
    LoadedRegistry,
    RegistryLoadReport,
    RegistrySummary,
)


class RegistryLoader(Protocol):
    """Parse a single registry file into a root mapping."""

    def load_mapping(
        self,
        path: Path,
        *,
        source_format: Literal["yaml", "json"],
        max_file_size_bytes: int,
    ) -> dict[str, Any]: ...


class RegistryCatalog(Protocol):
    """Read-only loaded registry catalog."""

    async def load(self) -> RegistryLoadReport: ...

    def get(self, registry_id: str) -> LoadedRegistry: ...

    def list(self) -> tuple[LoadedRegistry, ...]: ...

    def safe_summary(self) -> RegistrySummary: ...

    async def close(self) -> None: ...
