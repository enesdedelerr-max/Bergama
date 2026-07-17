"""Plugin manifest and capability declarations."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from bergama_strategy_sdk.permissions import PluginPermissions
from bergama_strategy_sdk.serialization import sha256_hex
from bergama_strategy_sdk.versions import VersionAxes


class PluginCapability(StrEnum):
    REQUIRES_STATE = "requires_state"
    SUPPORTS_REPLAY = "supports_replay"
    SUPPORTS_INCREMENTAL = "supports_incremental"
    SUPPORTS_BATCH = "supports_batch"
    SUPPORTS_STREAM = "supports_stream"
    SUPPORTS_TRAINING = "supports_training"


class StrategyPluginManifest(BaseModel):
    """Immutable plugin manifest validated at load time."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    manifest_schema_version: str = Field(default="1.0.0", min_length=1, max_length=32)
    strategy_id: str = Field(min_length=1, max_length=128)
    strategy_version: str = Field(min_length=1, max_length=64)
    sdk_schema_version: str = Field(min_length=1, max_length=32)
    runtime_protocol_version: str = Field(min_length=1, max_length=32)
    feature_schema_version: str = Field(min_length=1, max_length=32)
    config_schema_version: str = Field(min_length=1, max_length=32)
    author: str = Field(min_length=1, max_length=256)
    package_identity: str = Field(min_length=1, max_length=256)
    required_features: tuple[str, ...] = Field(default_factory=tuple)
    permissions: PluginPermissions = Field(default_factory=PluginPermissions.empty)
    capabilities: dict[str, bool] = Field(default_factory=dict)
    uses_experimental_api: bool = False

    @field_validator("required_features")
    @classmethod
    def unique_features(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        seen: set[str] = set()
        ordered: list[str] = []
        for feature in value:
            text = feature.strip()
            if not text:
                msg = "required feature identifiers must be non-empty"
                raise ValueError(msg)
            if text in seen:
                msg = f"duplicate required feature {text!r}"
                raise ValueError(msg)
            seen.add(text)
            ordered.append(text)
        return tuple(ordered)

    @field_validator("capabilities", mode="before")
    @classmethod
    def validate_capability_taxonomy(cls, value: object) -> dict[str, bool]:
        if not isinstance(value, dict):
            msg = "capabilities must be a mapping"
            raise TypeError(msg)
        allowed = {capability.value for capability in PluginCapability}
        cleaned: dict[str, bool] = {}
        for raw_key, raw_value in value.items():
            key = str(raw_key).strip()
            if key not in allowed:
                msg = f"unsupported capability {key!r}"
                raise ValueError(msg)
            # Reject truthy/falsy coercion — require exact bool before pydantic converts.
            if type(raw_value) is not bool:
                msg = f"capability {key!r} must be an exact bool"
                raise TypeError(msg)
            cleaned[key] = raw_value
        return {key: cleaned[key] for key in sorted(cleaned)}

    @model_validator(mode="after")
    def validate_capabilities(self) -> StrategyPluginManifest:
        if self.capabilities.get(PluginCapability.SUPPORTS_TRAINING.value, False):
            msg = "supports_training must remain false for #406"
            raise ValueError(msg)
        if not self.capabilities.get(PluginCapability.SUPPORTS_REPLAY.value, True):
            msg = "supports_replay must be true for #406"
            raise ValueError(msg)
        return self

    def version_axes(self) -> VersionAxes:
        return VersionAxes(
            sdk_schema_version=self.sdk_schema_version,
            runtime_protocol_version=self.runtime_protocol_version,
            strategy_version=self.strategy_version,
            feature_schema_version=self.feature_schema_version,
            config_schema_version=self.config_schema_version,
        )

    def fingerprint(self) -> str:
        return sha256_hex(
            {
                "author": self.author,
                "capabilities": dict(sorted(self.capabilities.items())),
                "config_schema_version": self.config_schema_version,
                "feature_schema_version": self.feature_schema_version,
                "manifest_schema_version": self.manifest_schema_version,
                "package_identity": self.package_identity,
                "permissions": self.permissions.model_dump(mode="python"),
                "required_features": list(self.required_features),
                "runtime_protocol_version": self.runtime_protocol_version,
                "sdk_schema_version": self.sdk_schema_version,
                "strategy_id": self.strategy_id,
                "strategy_version": self.strategy_version,
                "uses_experimental_api": self.uses_experimental_api,
            }
        )
