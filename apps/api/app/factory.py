"""FastAPI application factory."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, FastAPI
from fastapi.openapi.utils import get_openapi

from app.core.config import AppSettings, get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.lifespan import lifespan
from app.middleware.request_context import RequestContextMiddleware
from app.routers import register_routers
from app.routers.health import router as health_router


def create_app(settings: AppSettings | None = None) -> FastAPI:
    """Build and configure the FastAPI application from typed settings.

    Ownership: ``configure_logging`` is called only here (not in main/lifespan).
    """
    resolved = settings or get_settings()
    configure_logging(resolved)

    docs_url = "/docs" if resolved.docs_enabled else None
    openapi_url = "/openapi.json" if resolved.openapi_enabled else None
    redoc_url = "/redoc" if resolved.docs_enabled else None

    application = FastAPI(
        title=resolved.app_name,
        version=resolved.app_version,
        debug=resolved.debug,
        description=(
            "Bergama Trading Platform API — Sprint 2 FastAPI runtime foundation. "
            "JWT bootstrap auth is local/test only; production identity will use OIDC."
        ),
        lifespan=lifespan,
        docs_url=docs_url,
        openapi_url=openapi_url,
        redoc_url=redoc_url,
    )
    application.state.settings = resolved
    application.add_middleware(RequestContextMiddleware)
    register_exception_handlers(application)

    # Probes stay unprefixed for Kubernetes / load-balancer conventions.
    application.include_router(health_router)

    api_router = APIRouter()
    register_routers(api_router, include_health=False)
    application.include_router(api_router, prefix=resolved.api_prefix)

    _install_openapi(application)
    return application


def _install_openapi(application: FastAPI) -> None:
    """Ensure Bearer security scheme is present for protected routes."""

    def custom_openapi() -> dict[str, Any]:
        if application.openapi_schema is not None:
            return application.openapi_schema
        schema = get_openapi(
            title=application.title,
            version=application.version,
            description=application.description,
            routes=application.routes,
        )
        components = schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})
        security_schemes["HTTPBearer"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Local/test bootstrap JWT (HS256). Not a production OIDC token.",
        }
        application.openapi_schema = schema
        return schema

    application.openapi = custom_openapi  # type: ignore[method-assign]
