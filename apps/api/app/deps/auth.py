"""FastAPI authentication dependencies (Issue #205)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.errors import MISSING_TOKEN, AuthError
from app.core.config import AppSettings
from app.schemas.auth import AuthenticatedPrincipal
from app.services.token_service import TokenService

_bearer_scheme = HTTPBearer(auto_error=False)


def get_app_settings(request: Request) -> AppSettings:
    """Resolve settings from application state."""
    settings: AppSettings = request.app.state.settings
    return settings


def get_token_service(settings: Annotated[AppSettings, Depends(get_app_settings)]) -> TokenService:
    """Build a request-scoped token service from settings."""
    return TokenService(settings)


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
