"""Application lifespan — startup and shutdown hooks."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import AppSettings
from app.core.container import AppContainer
from app.core.logging import get_logger, structured_extra
from app.health.runtime_state import RuntimeLifecycleState
from app.health.service import log_startup_state_change

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
            kafka_enabled=settings.kafka.enabled,
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
    """FastAPI lifespan using the same container attached at factory time."""
    container = getattr(app.state, "container", None)
    if not isinstance(container, AppContainer):
        msg = "application container is not configured on app.state.container"
        raise RuntimeError(msg)
    settings = container.settings
    runtime = container.runtime_state
    previous = runtime.state
    try:
        await on_startup(settings)
        if container.kafka_runtime is not None:
            await container.kafka_runtime.start()
        runtime.mark_started()
        log_startup_state_change(runtime, previous=previous)
    except Exception:
        if container.kafka_runtime is not None:
            await container.kafka_runtime.stop()
        runtime.mark_failed()
        log_startup_state_change(runtime, previous=previous)
        raise
    try:
        yield
    finally:
        stopping_from = runtime.state
        runtime.mark_stopping()
        if stopping_from is not RuntimeLifecycleState.STOPPING:
            log_startup_state_change(runtime, previous=stopping_from)
        await on_shutdown(settings)
        # aclose stops kafka (workers → consumers → producer) then exit stack.
        await container.aclose()
        runtime.mark_stopped()
        log_startup_state_change(runtime, previous=RuntimeLifecycleState.STOPPING)
