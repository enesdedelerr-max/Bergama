"""HTTP routers package."""

from fastapi import APIRouter

from app.routers.auth import router as auth_router
from app.routers.health import router as health_router


def register_routers(api_router: APIRouter, *, include_health: bool = True) -> None:
    """Register HTTP routers on an aggregate API router."""
    if include_health:
        api_router.include_router(health_router)
    api_router.include_router(auth_router)
