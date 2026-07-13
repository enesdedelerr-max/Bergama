"""Application lifespan hooks."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.settings import Settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run startup and shutdown side effects for the API process."""
    settings: Settings = app.state.settings
    logger.info(
        "startup complete",
        extra={
            "app_name": settings.app_name,
            "environment": settings.environment,
        },
    )
    yield
    logger.info("shutdown complete")
