"""Feature Platform settings — disabled by default.

Nested under AppSettings as ``feature_platform`` (``BERGAMA_FEATURE_PLATFORM__*``).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FeaturePlatformSettings(BaseModel):
    """Typed Feature Platform configuration."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    enabled: bool = False
    feature_schema_version: str = Field(default="1.0.0", min_length=1, max_length=32)

    def safe_summary(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "feature_schema_version": self.feature_schema_version,
        }
