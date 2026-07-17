"""#406 Strategy SDK Runtime settings.

Disabled by default. Separate from #401 StrategySettings — enabling this does not
implicitly migrate or replace the legacy Strategy Engine runtime.
"""

from __future__ import annotations

from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrategySdkRuntimeSettings(BaseModel):
    """Typed #406 SDK runtime configuration."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    enabled: bool = False
    runtime_protocol_version: str = Field(default="1.0.0", min_length=1, max_length=32)
    sdk_schema_version: str = Field(default="1.0.0", min_length=1, max_length=32)
    feature_schema_version: str = Field(default="1.0.0", min_length=1, max_length=32)
    config_schema_version: str = Field(default="1.0.0", min_length=1, max_length=32)
    allow_experimental: bool = False
    legacy_adapter_enabled: bool = False
    register_reference_plugin: bool = True
    execution_timeout_ms: int = Field(default=5_000, ge=1, le=300_000)
    max_feature_payload_bytes: int = Field(default=65_536, ge=1, le=1_048_576)
    max_output_bytes: int = Field(default=16_384, ge=1, le=1_048_576)
    max_safe_metadata_bytes: int = Field(default=4_096, ge=1, le=65_536)
    max_state_bytes: int = Field(default=16_384, ge=1, le=1_048_576)
    max_plugin_failures_per_batch: int = Field(default=32, ge=1, le=128)
    max_required_features: int = Field(default=64, ge=1, le=256)
    max_manifest_bytes: int = Field(default=32_768, ge=1, le=1_048_576)
    audit_max_records: int = Field(default=10_000, ge=1, le=1_000_000)
    max_plugins_per_session: int = Field(default=16, ge=1, le=128)
    trusted_plugin_allowlist: tuple[str, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def validate_allowlist(self) -> Self:
        seen: set[str] = set()
        for plugin_key in self.trusted_plugin_allowlist:
            text = plugin_key.strip()
            if not text:
                msg = "trusted_plugin_allowlist entries must be non-empty"
                raise ValueError(msg)
            if text in seen:
                msg = f"duplicate trusted plugin allowlist entry {text!r}"
                raise ValueError(msg)
            seen.add(text)
        return self

    def safe_summary(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "runtime_protocol_version": self.runtime_protocol_version,
            "sdk_schema_version": self.sdk_schema_version,
            "feature_schema_version": self.feature_schema_version,
            "config_schema_version": self.config_schema_version,
            "allow_experimental": self.allow_experimental,
            "legacy_adapter_enabled": self.legacy_adapter_enabled,
            "register_reference_plugin": self.register_reference_plugin,
            "execution_timeout_ms": self.execution_timeout_ms,
            "max_plugins_per_session": self.max_plugins_per_session,
            "trusted_plugin_allowlist": list(self.trusted_plugin_allowlist),
        }
