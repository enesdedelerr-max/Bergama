"""Liveness, readiness and startup health routers (Issue #207)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from app.core.providers import provide_health_service
from app.deps.container import get_app_container
from app.health.service import HealthService
from app.schemas.health import LivenessResponse, ReadinessResponse, StartupResponse

router = APIRouter(tags=["health"])

_NO_STORE = {"Cache-Control": "no-store"}


def get_health_service(request: Request) -> HealthService:
    """Resolve the application-scoped health service."""
    return provide_health_service(get_app_container(request))


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    responses={200: {"description": "Process is alive"}},
)
async def health_live(
    response: Response,
    health_service: Annotated[HealthService, Depends(get_health_service)],
) -> LivenessResponse:
    """Liveness probe — process up; no external dependency calls."""
    response.headers["Cache-Control"] = "no-store"
    return health_service.liveness()


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={
        200: {"description": "Ready or degraded (required dependencies pass)"},
        503: {"description": "Not ready — required dependency failure"},
    },
)
async def health_ready(
    health_service: Annotated[HealthService, Depends(get_health_service)],
) -> JSONResponse:
    """Readiness probe — required dependencies must pass."""
    body, status_code = await health_service.readiness()
    return JSONResponse(
        content=body.model_dump(mode="json"),
        status_code=status_code,
        headers=_NO_STORE,
    )


@router.get(
    "/health/startup",
    response_model=StartupResponse,
    responses={
        200: {"description": "Application startup completed"},
        503: {"description": "Still starting or startup failed"},
    },
)
async def health_startup(
    health_service: Annotated[HealthService, Depends(get_health_service)],
) -> JSONResponse:
    """Startup probe — reflects container lifecycle state."""
    body, status_code = health_service.startup()
    return JSONResponse(
        content=body.model_dump(mode="json"),
        status_code=status_code,
        headers=_NO_STORE,
    )


@router.get(
    "/health",
    response_model=LivenessResponse,
    deprecated=True,
    responses={200: {"description": "Deprecated alias of /health/live"}},
)
async def health_legacy(
    response: Response,
    health_service: Annotated[HealthService, Depends(get_health_service)],
) -> LivenessResponse:
    """Deprecated alias of ``/health/live``."""
    response.headers["Cache-Control"] = "no-store"
    return health_service.liveness()


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    deprecated=True,
    responses={
        200: {"description": "Deprecated alias of /health/ready"},
        503: {"description": "Not ready"},
    },
)
async def ready_legacy(
    health_service: Annotated[HealthService, Depends(get_health_service)],
) -> JSONResponse:
    """Deprecated alias of ``/health/ready``."""
    body, status_code = await health_service.readiness()
    return JSONResponse(
        content=body.model_dump(mode="json"),
        status_code=status_code,
        headers=_NO_STORE,
    )
