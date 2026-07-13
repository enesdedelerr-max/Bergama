"""Liveness and readiness endpoints."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.deps import LoggerDep, SettingsDep

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"] = Field(default="ok")


class ReadyResponse(BaseModel):
    status: Literal["ready"] = Field(default="ready")
    environment: str


@router.get("/health", response_model=HealthResponse)
async def health(logger: LoggerDep) -> HealthResponse:
    """Liveness probe — process is up."""
    logger.debug("health check")
    return HealthResponse()


@router.get("/ready", response_model=ReadyResponse)
async def ready(settings: SettingsDep, logger: LoggerDep) -> ReadyResponse:
    """Readiness probe — runtime config loaded; no external deps in #201."""
    logger.debug("readiness check", extra={"environment": settings.environment})
    return ReadyResponse(environment=settings.environment)
