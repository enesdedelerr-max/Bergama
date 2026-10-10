"""FastAPI application factory."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.core.config import AppSettings, get_settings
from app.core.container import AppContainer, build_container
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.deps.container import attach_container
from app.lifespan import lifespan
from app.middleware.request_context import RequestContextMiddleware
from app.routers import register_routers
from app.routers.health import router as health_router

_CORS_ALLOW_METHODS: tuple[str, ...] = ("GET", "OPTIONS", "POST")
_CORS_ALLOW_HEADERS: tuple[str, ...] = ("Authorization", "Content-Type")
_CORS_MAX_AGE_HEADER = b"access-control-max-age"


class _OmitCorsMaxAgeMiddleware:
    """Strip Starlette's default Access-Control-Max-Age so Max-Age is omitted."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = [
                    (key, value)
                    for key, value in message.get("headers", [])
                    if key.lower() != _CORS_MAX_AGE_HEADER
                ]
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_wrapper)


def create_app(
    settings: AppSettings | None = None,
    container: AppContainer | None = None,
) -> FastAPI:
    """Build and configure the FastAPI application from a typed container.

    Ownership:
    - ``configure_logging`` is called only here (not in main/lifespan).
    - Long-lived dependencies live on ``app.state.container`` only.
    - If ``container`` is supplied it is used as-is (never rebuilt).
    - If both ``settings`` and ``container`` are supplied, they must be the
      same settings instance.
    """
    resolved_container = _resolve_container(settings=settings, container=container)
    resolved = resolved_container.settings
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
    attach_container(application.state, resolved_container)
    application.add_middleware(RequestContextMiddleware)
    _install_cors_middleware(application, resolved)
    register_exception_handlers(application)

    # Probes stay unprefixed for Kubernetes / load-balancer conventions.
    application.include_router(health_router)

    api_router = APIRouter()
    register_routers(api_router, include_health=False)
    application.include_router(api_router, prefix=resolved.api_prefix)

    _install_openapi(application)
    return application


def _resolve_container(
    *,
    settings: AppSettings | None,
    container: AppContainer | None,
) -> AppContainer:
    if container is not None and settings is not None:
        if container.settings is not settings:
            msg = (
                "settings and container.settings must be the same instance "
                "when both are passed to create_app"
            )
            raise ValueError(msg)
        return container
    if container is not None:
        return container
    resolved_settings = settings if settings is not None else get_settings()
    return build_container(resolved_settings)


def _install_cors_middleware(application: FastAPI, settings: AppSettings) -> None:
    """Install explicit CORS allowlist; empty allowlist denies all cross-origin.

    Max-Age is not product-configured. Starlette's default Max-Age header is
    stripped so Access-Control-Max-Age is omitted on the wire.
    """
    origins = settings.cors.normalized_origins()
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=list(_CORS_ALLOW_METHODS),
        allow_headers=list(_CORS_ALLOW_HEADERS),
        expose_headers=[],
    )
    # Outer wrapper: remove Starlette default Access-Control-Max-Age.
    application.add_middleware(_OmitCorsMaxAgeMiddleware)


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
