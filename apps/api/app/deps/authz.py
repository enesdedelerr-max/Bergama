"""Minimal product authorization dependencies (Sprint 14 WS3)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.core.security import INTELLIGENCE_RUNS_READ_SCOPE
from app.deps.auth import get_current_principal
from app.intelligence_runs.product_errors import insufficient_scope
from app.schemas.auth import AuthenticatedPrincipal


def require_intelligence_runs_read(
    principal: Annotated[AuthenticatedPrincipal, Depends(get_current_principal)],
) -> AuthenticatedPrincipal:
    """Require dedicated ``intelligence:runs:read``; ``api:read`` alone is insufficient."""
    if INTELLIGENCE_RUNS_READ_SCOPE not in principal.scopes:
        raise insufficient_scope()
    return principal
