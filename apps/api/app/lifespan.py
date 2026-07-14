"""Application lifespan — startup and shutdown hooks."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import AppSettings
from app.core.logging import get_logger, structured_extra

logger = get_logger(__name__)


def _lifecycle_extra(settings: AppSettings, *, event: str) -> dict[str, object]:
    return structured_extra(
        event=event,
        source="lifespan",
        service=settings.service_name,
        version=settings.app_version,
        environment=settings.environment.value,
    )


async def on_startup(settings: AppSettings) -> None:
    """Emit starting/started lifecycle logs without dumping settings or secrets."""
    flags = settings.secrets.safe_summary()
    logger.info(
        "application starting",
        extra=_lifecycle_extra(settings, event="application.starting"),
    )
    logger.info(
        "application started",
        extra=structured_extra(
            event="application.started",
            source="lifespan",
            service=settings.service_name,
            version=settings.app_version,
            environment=settings.environment.value,
            app_secret_key_configured=flags["app_secret_key_configured"],
            bootstrap_jwt_signing_key_configured=flags["bootstrap_jwt_signing_key_configured"],
        ),
    )


async def on_shutdown(settings: AppSettings) -> None:
    """Emit stopping/stopped lifecycle logs without dumping settings."""
    logger.info(
        "application stopping",
        extra=_lifecycle_extra(settings, event="application.stopping"),
    )
    logger.info(
        "application stopped",
        extra=_lifecycle_extra(settings, event="application.stopped"),
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """FastAPI lifespan context separating startup and shutdown."""
    settings: AppSettings = app.state.settings
    await on_startup(settings)
    try:
        yield
    finally:
        await on_shutdown(settings)
