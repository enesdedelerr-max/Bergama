"""FastAPI authentication dependencies (Issue #205 / #206)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.errors import MISSING_TOKEN, AuthError
from app.core.config import AppSettings
from app.core.providers import provide_settings, provide_token_service
from app.deps.container import get_app_container
from app.schemas.auth import AuthenticatedPrincipal
from app.services.token_service import TokenService

_bearer_scheme = HTTPBearer(auto_error=False)


def get_app_settings(request: Request) -> AppSettings:
    """Resolve settings from the application container."""
    return provide_settings(get_app_container(request))


def get_token_service(request: Request) -> TokenService:
    """Resolve the application-scoped token service from the container."""
    return provide_token_service(get_app_container(request))


async def get_current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> AuthenticatedPrincipal:
    """Require a valid Bearer access token and return the typed principal."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise MISSING_TOKEN
    token = credentials.credentials.strip()
    if not token:
        raise MISSING_TOKEN
    try:
        return token_service.authenticate(token)
    except AuthError:
        raise
