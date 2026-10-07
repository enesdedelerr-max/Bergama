"""PostgreSQL product OLTP settings (Sprint 14 WS1).

DSN is the sole product source of truth for SQLAlchemy/psycopg connectivity.
Health-check `postgres_host` / `postgres_port` remain TCP probes only.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

_PSYCOPG_DSN_PREFIX = "postgresql+psycopg://"


class DatabaseSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    url: str | None = Field(
        default=None,
        description="Sync SQLAlchemy DSN using the psycopg 3 driver.",
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if not text:
            return None
        if not text.startswith(_PSYCOPG_DSN_PREFIX):
            msg = f"database.url must use the sync psycopg driver prefix {_PSYCOPG_DSN_PREFIX!r}"
            raise ValueError(msg)
        return text

    def safe_summary(self) -> dict[str, Any]:
        return {
            "configured": self.url is not None,
            "driver": "postgresql+psycopg" if self.url is not None else None,
        }
