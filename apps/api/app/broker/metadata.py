"""Bounded safe metadata normalization for broker → OMS (#405)."""

from __future__ import annotations

from collections.abc import Mapping

from app.portfolio.models import validate_safe_metadata


def normalize_provider_metadata(raw: Mapping[str, object] | None) -> dict[str, str]:
    """Convert provider key/value pairs into bounded safe_metadata.

    Raw provider payloads/SDK objects must never reach OMS. Only string tokens
    that pass the shared safe_metadata validator are retained.
    """
    if raw is None:
        return {}
    cleaned: dict[str, str] = {}
    for key, value in raw.items():
        if value is None:
            continue
        cleaned[str(key)] = str(value)
    return validate_safe_metadata(cleaned)
