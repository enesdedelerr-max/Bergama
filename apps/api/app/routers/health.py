"""Liveness and readiness routers."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"] = Field(default="ok")


class ReadyResponse(BaseModel):
    status: Literal["ready"] = Field(default="ready")
    environment: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe — process is up."""
    return HealthResponse()


@router.get("/ready", response_model=ReadyResponse)
async def ready() -> ReadyResponse:
    """Readiness probe — runtime is ready (no external deps in #201)."""
    settings: Settings = get_settings()
    return ReadyResponse(environment=settings.environment)
