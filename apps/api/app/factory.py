"""FastAPI application factory."""

from __future__ import annotations

from fastapi import APIRouter, FastAPI

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.lifespan import lifespan
from app.routers import register_routers


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the FastAPI application."""
    resolved = settings or get_settings()
    configure_logging(level=resolved.log_level, json_logs=resolved.log_json)

    application = FastAPI(
        title=resolved.app_name,
        version=resolved.app_version,
        description=(
            "Bergama Trading Platform API — FastAPI runtime bootstrap (Sprint 2 Issue #201)."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        openapi_url="/openapi.json",
        redoc_url="/redoc",
    )
    application.state.settings = resolved

    api_router = APIRouter()
    register_routers(api_router)
    application.include_router(api_router)
    return application
