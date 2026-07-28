"""Premarket Intelligence settings — disabled by default.

Nested under AppSettings as ``premarket`` (``BERGAMA_PREMARKET__*``).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class PremarketSettings(BaseModel):
    """Typed Premarket Intelligence configuration."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    enabled: bool = False

    def safe_summary(self) -> dict[str, Any]:
        return {"enabled": self.enabled}
