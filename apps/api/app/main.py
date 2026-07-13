"""FastAPI application factory and process entrypoint."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from app.api.router import api_router
from app.config.settings import Settings, get_settings
from app.core.lifespan import lifespan
from app.core.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI application."""
    resolved = settings or get_settings()
    configure_logging(level=resolved.log_level, json_logs=resolved.log_json)

    application = FastAPI(
        title=resolved.app_name,
        version="0.2.0",
        description="Bergama Trading Platform API — FastAPI runtime foundation (Sprint 2).",
        lifespan=lifespan,
        docs_url="/docs",
        openapi_url="/openapi.json",
        redoc_url="/redoc",
    )
    application.state.settings = resolved
    application.include_router(api_router)
    return application


app = create_app()


def run() -> None:
    """Console script entrypoint: `uv run app`."""
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        factory=False,
    )


if __name__ == "__main__":
    run()
