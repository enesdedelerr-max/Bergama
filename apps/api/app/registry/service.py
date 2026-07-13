"""Container-owned read-only registry service."""

from __future__ import annotations

import builtins
import hashlib
import time
from pathlib import Path
from typing import Literal

from app.core.clock import Clock, SystemClock
from app.core.logging import get_logger, structured_extra
from app.core.registry_settings import RegistrySettings
from app.registry.canonical import compute_content_fingerprint
from app.registry.errors import (
    RegistryDuplicateIdError,
    RegistryError,
    RegistryNotFoundError,
    RegistryNotLoadedError,
    RegistryPathNotFoundError,
    RegistryPathOutsideRootError,
    RegistrySymlinkRejectedError,
    RegistryUnsupportedExtensionError,
)
from app.registry.loaders import load_registry_mapping
from app.registry.models import (
    LoadedRegistry,
    RegistryLoadReport,
    RegistrySummary,
)
from app.registry.validation import (
    validate_document_mapping,
    validate_required_ids,
    validate_shallow_dependencies,
)

logger = get_logger(__name__)


class RegistryService:
    """Discover, validate and expose local registry documents."""

    def __init__(
        self,
        settings: RegistrySettings,
        *,
        clock: Clock | None = None,
    ) -> None:
        self._settings = settings
        self._clock = clock if clock is not None else SystemClock()
        self._registries: tuple[LoadedRegistry, ...] = ()
        self._by_id: dict[str, LoadedRegistry] = {}
        self._loaded = False
        self._closed = False

    @property
    def settings(self) -> RegistrySettings:
        return self._settings

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    async def load(self) -> RegistryLoadReport:
        """Load registries from configured paths. Idempotent replace of catalog."""
        if self._closed:
            raise RegistryNotLoadedError("registry service is closed")
        started = time.perf_counter()
        if not self._settings.enabled:
            self._registries = ()
            self._by_id = {}
            self._loaded = True
            duration_ms = round((time.perf_counter() - started) * 1000.0, 3)
            logger.info(
                "registry load skipped (disabled)",
                extra=structured_extra(
                    event="registry.loaded",
                    source="registry",
                    enabled=False,
                    count=0,
                    duration_ms=duration_ms,
                ),
            )
            return RegistryLoadReport(
                registries=(),
                duration_ms=duration_ms,
                schema_major=self._settings.supported_schema_major,
            )

        logger.info(
            "registry loading",
            extra=structured_extra(
                event="registry.loading",
                source="registry",
                path_count=len(self._settings.paths),
                required_count=len(self._settings.required_registry_ids),
            ),
        )
        try:
            files = self._discover_files()
            loaded: list[LoadedRegistry] = []
            seen_ids: dict[str, Path] = {}
            for path, source_format in files:
                mapping = load_registry_mapping(
                    path,
                    source_format=source_format,
                    max_file_size_bytes=self._settings.max_file_size_bytes,
                )
                document = validate_document_mapping(
                    mapping,
                    supported_schema_major=self._settings.supported_schema_major,
                )
                registry_id = document.registry_id
                if registry_id in seen_ids:
                    raise RegistryDuplicateIdError(
                        f"duplicate registry id {registry_id!r}",
                        path=str(path),
                    )
                seen_ids[registry_id] = path
                fingerprint = compute_content_fingerprint(document)
                loaded.append(
                    LoadedRegistry(
                        document=document,
                        source_path=path,
                        source_format=source_format,
                        loaded_at=self._clock.now(),
                        content_fingerprint=fingerprint,
                    )
                )
            ordered = tuple(sorted(loaded, key=lambda item: item.registry_id))
            validate_required_ids(ordered, self._settings.required_registry_ids)
            validate_shallow_dependencies(ordered)
        except RegistryError as exc:
            logger.error(
                "registry load failed",
                extra=structured_extra(
                    event="registry.load_failed",
                    source="registry",
                    error_code=exc.code,
                    path=exc.path,
                ),
            )
            raise
        except Exception:
            logger.error(
                "registry validation failed",
                exc_info=True,
                extra=structured_extra(
                    event="registry.validation_failed",
                    source="registry",
                ),
            )
            raise

        self._registries = ordered
        self._by_id = {item.registry_id: item for item in ordered}
        self._loaded = True
        duration_ms = round((time.perf_counter() - started) * 1000.0, 3)
        summary = self.safe_summary()
        logger.info(
            "registry loaded",
            extra=structured_extra(
                event="registry.loaded",
                source="registry",
                enabled=True,
                count=summary.count,
                registry_ids=list(summary.registry_ids),
                schema_major=summary.schema_major,
                fingerprint_prefix=(summary.aggregate_fingerprint or "")[:12] or None,
                duration_ms=duration_ms,
            ),
        )
        return RegistryLoadReport(
            registries=ordered,
            duration_ms=duration_ms,
            schema_major=self._settings.supported_schema_major,
        )

    def get(self, registry_id: str) -> LoadedRegistry:
        if not self._loaded:
            raise RegistryNotLoadedError("registry catalog is not loaded")
        try:
            return self._by_id[registry_id]
        except KeyError as exc:
            raise RegistryNotFoundError(f"registry not found: {registry_id!r}") from exc

    def list(self) -> tuple[LoadedRegistry, ...]:
        if not self._loaded:
            raise RegistryNotLoadedError("registry catalog is not loaded")
        return self._registries

    def safe_summary(self) -> RegistrySummary:
        if not self._loaded:
            return RegistrySummary(
                enabled=self._settings.enabled,
                loaded=False,
                count=0,
                required_count=len(self._settings.required_registry_ids),
                schema_major=self._settings.supported_schema_major,
                registry_ids=(),
                aggregate_fingerprint=None,
            )
        ids = tuple(item.registry_id for item in self._registries)
        aggregate = None
        if self._registries:
            joined = "|".join(
                f"{item.registry_id}:{item.content_fingerprint}" for item in self._registries
            )
            aggregate = hashlib.sha256(joined.encode("utf-8")).hexdigest()
        return RegistrySummary(
            enabled=self._settings.enabled,
            loaded=True,
            count=len(self._registries),
            required_count=len(self._settings.required_registry_ids),
            schema_major=self._settings.supported_schema_major,
            registry_ids=ids,
            aggregate_fingerprint=aggregate,
        )

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._registries = ()
        self._by_id = {}
        self._loaded = False

    def _discover_files(self) -> builtins.list[tuple[Path, Literal["yaml", "json"]]]:
        discovered: builtins.list[tuple[Path, Literal["yaml", "json"]]] = []
        seen_resolved: set[Path] = set()
        roots = [Path(p).expanduser() for p in self._settings.paths]
        for root in sorted(roots, key=lambda p: str(p)):
            if not root.exists():
                raise RegistryPathNotFoundError(
                    f"registry path not found: {root}",
                    path=str(root),
                )
            if root.is_symlink() and not self._settings.allow_symlinks:
                raise RegistrySymlinkRejectedError(
                    f"symlink rejected: {root}",
                    path=str(root),
                )
            root_resolved = root.resolve()
            if root.is_file():
                self._accept_file(
                    root,
                    root_resolved,
                    root_resolved.parent,
                    discovered,
                    seen_resolved,
                )
                continue
            if not root.is_dir():
                raise RegistryPathNotFoundError(
                    f"registry path is not a directory or file: {root}",
                    path=str(root),
                )
            candidates = (
                sorted(root.rglob("*")) if self._settings.recursive else sorted(root.iterdir())
            )
            for candidate in candidates:
                if candidate.name.startswith("."):
                    continue
                if candidate.is_dir():
                    continue
                self._accept_file(
                    candidate,
                    candidate.resolve(),
                    root_resolved,
                    discovered,
                    seen_resolved,
                )
        return discovered

    def _accept_file(
        self,
        candidate: Path,
        resolved: Path,
        root_resolved: Path,
        discovered: builtins.list[tuple[Path, Literal["yaml", "json"]]],
        seen_resolved: set[Path],
    ) -> None:
        if candidate.is_symlink() and not self._settings.allow_symlinks:
            raise RegistrySymlinkRejectedError(
                f"symlink rejected: {candidate}",
                path=str(candidate),
            )
        try:
            resolved.relative_to(root_resolved)
        except ValueError as exc:
            raise RegistryPathOutsideRootError(
                "registry path escapes configured root",
                path=str(candidate),
            ) from exc
        if resolved in seen_resolved:
            raise RegistryDuplicateIdError(
                f"duplicate source file {resolved}",
                path=str(candidate),
            )
        ext = candidate.suffix.lower()
        if ext not in self._settings.allowed_extensions:
            if self._settings.fail_on_unknown_files:
                raise RegistryUnsupportedExtensionError(
                    f"unsupported registry extension {ext!r}",
                    path=str(candidate),
                )
            return
        source_format: Literal["yaml", "json"] = "json" if ext == ".json" else "yaml"
        seen_resolved.add(resolved)
        discovered.append((resolved, source_format))
