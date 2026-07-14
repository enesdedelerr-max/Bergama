"""Application lifespan — startup and shutdown hooks."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import AppSettings

logger = logging.getLogger(__name__)


async def on_startup(settings: AppSettings) -> None:
    """Run process startup side effects."""
    summary = settings.safe_summary()
    logger.info(
        "startup complete env=%s service=%s",
        summary["environment"],
        summary["service_name"],
    )


async def on_shutdown() -> None:
    """Run process shutdown side effects."""
    logger.info("shutdown complete")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """FastAPI lifespan context separating startup and shutdown."""
    settings: AppSettings = app.state.settings
    await on_startup(settings)
    try:
        yield
    finally:
        await on_shutdown()
