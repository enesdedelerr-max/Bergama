"""Nested registry loader settings (Issue #209)."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RegistrySettings(BaseModel):
    """Local filesystem registry loading. Disabled by default."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    paths: list[str] = Field(default_factory=list)
    required_registry_ids: list[str] = Field(default_factory=list)
    supported_schema_major: int = Field(default=1, ge=1)
    fail_on_unknown_files: bool = True
    max_file_size_bytes: int = Field(default=1_048_576, gt=0)
    allowed_extensions: list[str] = Field(default_factory=lambda: [".yaml", ".yml", ".json"])
    load_on_startup: bool = True
    recursive: bool = False
    allow_symlinks: bool = False
    health_required: bool = False

    @field_validator("paths", mode="before")
    @classmethod
    def parse_paths(cls, value: object) -> object:
        if value is None:
            return []
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            if text.startswith("["):
                return value
            return [part.strip() for part in text.split(",") if part.strip()]
        return value

    @field_validator("required_registry_ids", mode="before")
    @classmethod
    def parse_required_ids(cls, value: object) -> object:
        if value is None:
            return []
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            if text.startswith("["):
                return value
            return [part.strip() for part in text.split(",") if part.strip()]
        return value

    @field_validator("allowed_extensions", mode="before")
    @classmethod
    def parse_extensions(cls, value: object) -> object:
        if value is None:
            return [".yaml", ".yml", ".json"]
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return [".yaml", ".yml", ".json"]
            if text.startswith("["):
                return value
            return [part.strip() for part in text.split(",") if part.strip()]
        return value

    @field_validator("allowed_extensions")
    @classmethod
    def normalize_extensions(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for item in value:
            ext = item.strip().lower()
            if not ext.startswith("."):
                ext = f".{ext}"
            if ext not in seen:
                seen.add(ext)
                normalized.append(ext)
        if not normalized:
            msg = "allowed_extensions must be non-empty"
            raise ValueError(msg)
        return normalized

    @field_validator("paths")
    @classmethod
    def reject_blank_paths(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for path in value:
            text = path.strip()
            if not text:
                msg = "registry paths must be non-empty"
                raise ValueError(msg)
            cleaned.append(text)
        return cleaned

    @model_validator(mode="after")
    def validate_semantics(self) -> Self:
        if len(self.required_registry_ids) != len(set(self.required_registry_ids)):
            msg = "required_registry_ids must be unique"
            raise ValueError(msg)
        if self.enabled and not self.paths:
            msg = "BERGAMA_REGISTRY__PATHS must be non-empty when registry is enabled"
            raise ValueError(msg)
        # Guard against accidental secret-path configuration.
        forbidden_markers = (".secrets", "secrets.env", "/secrets/")
        for path in self.paths:
            lowered = path.lower().replace("\\", "/")
            if any(marker in lowered for marker in forbidden_markers):
                msg = f"registry path must not reference secret files: {path!r}"
                raise ValueError(msg)
        return self

    def safe_summary(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "path_count": len(self.paths),
            "required_count": len(self.required_registry_ids),
            "supported_schema_major": self.supported_schema_major,
            "fail_on_unknown_files": self.fail_on_unknown_files,
            "max_file_size_bytes": self.max_file_size_bytes,
            "allowed_extensions": list(self.allowed_extensions),
            "load_on_startup": self.load_on_startup,
            "recursive": self.recursive,
            "allow_symlinks": self.allow_symlinks,
            "health_required": self.health_required,
        }
