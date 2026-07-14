"""Application deployment environment enumeration."""

from __future__ import annotations

from enum import StrEnum


class AppEnvironment(StrEnum):
    """Runtime profile. Unknown values fail Pydantic validation."""

    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"

    @property
    def loads_dotenv(self) -> bool:
        """Only local development may load a `.env` file."""
        return self is AppEnvironment.LOCAL

    @property
    def is_production_like(self) -> bool:
        """Staging and production share stricter defaults."""
        return self in {AppEnvironment.STAGING, AppEnvironment.PRODUCTION}
