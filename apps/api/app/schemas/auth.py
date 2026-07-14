"""Auth request/response schemas and typed JWT claims (Issue #205)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.security import TOKEN_TYPE_ACCESS


class BootstrapTokenRequest(BaseModel):
    """Local/test bootstrap grant only — no caller-controlled identity."""

    model_config = ConfigDict(extra="forbid")

    grant_type: Literal["bootstrap"] = "bootstrap"


class TokenResponse(BaseModel):
    """OAuth-style access-token response (bootstrap only)."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(gt=0)


class AuthMeResponse(BaseModel):
    """Protected smoke response — no business data."""

    subject: str
    roles: list[str]
    scopes: list[str]


class AccessTokenClaims(BaseModel):
    """Validated JWT access-token claims."""

    model_config = ConfigDict(extra="forbid")

    sub: str = Field(min_length=1)
    iss: str = Field(min_length=1)
    aud: str = Field(min_length=1)
    iat: int
    nbf: int
    exp: int
    jti: str = Field(min_length=1)
    token_type: Literal["access"] = TOKEN_TYPE_ACCESS
    roles: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)
    environment: str | None = None

    @field_validator("sub", "iss", "aud", "jti")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            msg = "claim must be non-empty"
            raise ValueError(msg)
        return value.strip()


@dataclass(frozen=True, slots=True)
class AuthenticatedPrincipal:
    """Immutable validated caller — never holds the raw JWT."""

    subject: str
    roles: tuple[str, ...]
    scopes: tuple[str, ...]
    token_id: str
    issuer: str
    audience: str
