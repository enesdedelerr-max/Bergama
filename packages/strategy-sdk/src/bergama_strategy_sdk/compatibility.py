"""SDK API compatibility helpers."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from bergama_strategy_sdk.errors import StrategyCompatibilityError
from bergama_strategy_sdk.manifest import StrategyPluginManifest
from bergama_strategy_sdk.versions import VersionAxes, is_sdk_backward_compatible


class RuntimeCompatibilityPolicy(BaseModel):
    """Runtime-supported version axes for fail-closed validation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    sdk_schema_version: str = Field(default="1.0.0", min_length=1, max_length=32)
    runtime_protocol_version: str = Field(default="1.0.0", min_length=1, max_length=32)
    feature_schema_version: str = Field(default="1.0.0", min_length=1, max_length=32)
    config_schema_version: str = Field(default="1.0.0", min_length=1, max_length=32)
    allow_experimental: bool = False


def validate_manifest_compatibility(
    manifest: StrategyPluginManifest,
    *,
    policy: RuntimeCompatibilityPolicy,
) -> VersionAxes:
    if manifest.uses_experimental_api and not policy.allow_experimental:
        raise StrategyCompatibilityError(detail="experimental_api_not_allowed")
    axes = manifest.version_axes()
    if not is_sdk_backward_compatible(
        required=axes,
        supported_sdk_schema_version=policy.sdk_schema_version,
        supported_runtime_protocol_version=policy.runtime_protocol_version,
        supported_feature_schema_version=policy.feature_schema_version,
        supported_config_schema_version=policy.config_schema_version,
    ):
        raise StrategyCompatibilityError(detail="version_axes_incompatible")
    return axes
