"""FastAPI dependency providers."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, Request

from app.config.settings import Settings, get_settings
from app.core.logging import get_logger


def provide_settings() -> Settings:
    """Resolve application settings."""
    return get_settings()


def provide_logger(request: Request) -> logging.Logger:
    """Resolve a request-scoped application logger."""
    _ = request
    return get_logger("app")


SettingsDep = Annotated[Settings, Depends(provide_settings)]
LoggerDep = Annotated[logging.Logger, Depends(provide_logger)]
