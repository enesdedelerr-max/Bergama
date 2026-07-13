"""Liveness and readiness routers."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.deps.container import get_app_container

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
async def ready(request: Request) -> ReadyResponse:
    """Readiness probe — runtime config loaded (no external deps in #202)."""
    settings = get_app_container(request).settings
    return ReadyResponse(environment=settings.environment.value)
