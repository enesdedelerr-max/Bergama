"""HTTP routers package."""

from fastapi import APIRouter

from app.routers.health import router as health_router


def register_routers(api_router: APIRouter) -> None:
    """Register all HTTP routers on the aggregate API router."""
    api_router.include_router(health_router)
