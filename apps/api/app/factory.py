"""FastAPI application factory."""

from __future__ import annotations

from fastapi import APIRouter, FastAPI

from app.core.config import AppSettings, get_settings
from app.core.logging import configure_logging
from app.lifespan import lifespan
from app.routers import register_routers
from app.routers.health import router as health_router


def create_app(settings: AppSettings | None = None) -> FastAPI:
    """Build and configure the FastAPI application from typed settings."""
    resolved = settings or get_settings()
    configure_logging(level=resolved.log_level, json_logs=True)

    docs_url = "/docs" if resolved.docs_enabled else None
    openapi_url = "/openapi.json" if resolved.openapi_enabled else None
    redoc_url = "/redoc" if resolved.docs_enabled else None

    application = FastAPI(
        title=resolved.app_name,
        version=resolved.app_version,
        debug=resolved.debug,
        description="Bergama Trading Platform API — Sprint 2 FastAPI runtime foundation.",
        lifespan=lifespan,
        docs_url=docs_url,
        openapi_url=openapi_url,
        redoc_url=redoc_url,
    )
    application.state.settings = resolved

    # Probes stay unprefixed for Kubernetes / load-balancer conventions.
    application.include_router(health_router)

    api_router = APIRouter()
    register_routers(api_router, include_health=False)
    application.include_router(api_router, prefix=resolved.api_prefix)
    return application
