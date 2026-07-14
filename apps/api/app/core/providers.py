"""Explicit typed providers for AppContainer-owned dependencies."""

from __future__ import annotations

from app.core.clock import Clock, JtiGenerator
from app.core.config import AppSettings
from app.core.container import AppContainer
from app.health.service import HealthService
from app.services.token_service import TokenService


def provide_settings(container: AppContainer) -> AppSettings:
    """Return the container-owned settings instance."""
    return container.settings


def provide_clock(container: AppContainer) -> Clock:
    """Return the container-owned clock."""
    return container.clock


def provide_jti_generator(container: AppContainer) -> JtiGenerator:
    """Return the container-owned JTI generator."""
    return container.jti_generator


def provide_token_service(container: AppContainer) -> TokenService:
    """Return the container-owned token service."""
    return container.token_service


def provide_health_service(container: AppContainer) -> HealthService:
    """Return the container-owned health service."""
    return container.health_service
