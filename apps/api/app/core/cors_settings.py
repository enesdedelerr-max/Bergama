"""CORS allowlist settings for browser Client + Auth (Sprint 15 WS1 / #168)."""

from __future__ import annotations

from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator


def normalize_cors_origin(raw: str) -> str:
    """Validate and normalize one absolute origin (scheme://host[:port])."""
    text = raw.strip()
    if not text:
        msg = "CORS origin must be non-empty"
        raise ValueError(msg)
    if "*" in text:
        msg = "CORS wildcard origins are forbidden"
        raise ValueError(msg)
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"}:
        msg = "CORS origin must use http or https"
        raise ValueError(msg)
    if not parsed.hostname:
        msg = "CORS origin must include a host"
        raise ValueError(msg)
    if parsed.path not in {"", "/"}:
        msg = "CORS origin must not include a path"
        raise ValueError(msg)
    if parsed.params or parsed.query or parsed.fragment:
        msg = "CORS origin must not include query or fragment"
        raise ValueError(msg)
    if parsed.username is not None or parsed.password is not None:
        msg = "CORS origin must not include userinfo"
        raise ValueError(msg)
    if "@" in parsed.netloc:
        msg = "CORS origin must not include userinfo"
        raise ValueError(msg)
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def parse_cors_allowed_origins(raw: str | None) -> list[str]:
    """Parse comma-separated origins; empty/unset yields deny-all empty list."""
    if raw is None:
        return []
    text = raw.strip()
    if not text:
        return []
    origins: list[str] = []
    seen: set[str] = set()
    for part in text.split(","):
        piece = part.strip()
        if not piece:
            continue
        normalized = normalize_cors_origin(piece)
        if normalized not in seen:
            seen.add(normalized)
            origins.append(normalized)
    return origins


class CorsSettings(BaseModel):
    """Nested CORS configuration. Unset/empty denies all cross-origin access."""

    model_config = ConfigDict(extra="forbid")

    allowed_origins: str = Field(
        default="",
        description="Comma-separated absolute origins (BERGAMA_CORS__ALLOWED_ORIGINS).",
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def coerce_none(cls, value: object) -> object:
        if value is None:
            return ""
        return value

    def normalized_origins(self) -> list[str]:
        """Return validated origins; raises ValueError on invalid entries."""
        return parse_cors_allowed_origins(self.allowed_origins)

    def safe_summary(self) -> dict[str, object]:
        try:
            origins = self.normalized_origins()
            valid = True
            error: str | None = None
        except ValueError as exc:
            origins = []
            valid = False
            error = str(exc)
        return {
            "allowed_origin_count": len(origins),
            "allowed_origins_configured": bool(self.allowed_origins.strip()),
            "configuration_valid": valid,
            "configuration_error": error,
        }
