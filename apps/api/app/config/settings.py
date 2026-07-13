"""Environment-backed application settings (paper-safe defaults)."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="BERGAMA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="bergama-api")
    environment: Literal["paper", "sandbox", "live"] = Field(default="paper")
    debug: bool = Field(default=False)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    log_json: bool = Field(default=True)


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance for DI."""
    return Settings()
