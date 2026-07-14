"""Bootstrap JWT auth routes (Issue #205)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.auth.errors import BOOTSTRAP_DISABLED
from app.core.config import AppSettings
from app.core.logging import get_logger, structured_extra
from app.core.security import BOOTSTRAP_GRANT_TYPE
from app.deps.auth import get_app_settings, get_current_principal, get_token_service
from app.schemas.auth import (
    AuthenticatedPrincipal,
    AuthMeResponse,
    BootstrapTokenRequest,
    TokenResponse,
)
from app.services.token_service import TokenService

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_NO_STORE_HEADERS = {
    "Cache-Control": "no-store",
    "Pragma": "no-cache",
}


@router.post(
    "/token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Issue local bootstrap access token",
    description=(
        "Local/test only. Issues a fixed bootstrap identity JWT (HS256). "
        "Not available in staging or production — future auth uses OIDC."
    ),
)
def issue_bootstrap_token(
    response: Response,
    body: BootstrapTokenRequest,
    settings: Annotated[AppSettings, Depends(get_app_settings)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> TokenResponse:
    """Mint a bootstrap access token when bootstrap auth is enabled."""
    if not settings.bootstrap_auth_enabled:
        logger.warning(
            "bootstrap token endpoint disabled",
            extra=structured_extra(
                event="auth.bootstrap.disabled",
                error_code=BOOTSTRAP_DISABLED.code,
                source="auth_router",
            ),
        )
        raise BOOTSTRAP_DISABLED

    if body.grant_type != BOOTSTRAP_GRANT_TYPE:
        raise BOOTSTRAP_DISABLED

    for key, value in _NO_STORE_HEADERS.items():
        response.headers[key] = value
    return token_service.create_bootstrap_access_token()


@router.get(
    "/me",
    response_model=AuthMeResponse,
    summary="Return authenticated bootstrap principal",
)
def auth_me(
    principal: Annotated[AuthenticatedPrincipal, Depends(get_current_principal)],
) -> AuthMeResponse:
    """Protected smoke endpoint for JWT validation."""
    return AuthMeResponse(
        subject=principal.subject,
        roles=list(principal.roles),
        scopes=list(principal.scopes),
    )
