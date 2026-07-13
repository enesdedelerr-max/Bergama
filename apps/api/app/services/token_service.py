"""JWT access-token create/verify service (Issue #205)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Final
from uuid import uuid4

import jwt
from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    ImmatureSignatureError,
    InvalidAudienceError,
    InvalidIssuedAtError,
    InvalidIssuerError,
    InvalidSignatureError,
    InvalidTokenError,
    MissingRequiredClaimError,
)

from app.auth.errors import (
    EXPIRED_TOKEN,
    INVALID_AUDIENCE,
    INVALID_ISSUER,
    INVALID_TOKEN,
    INVALID_TOKEN_TYPE,
    AuthError,
)
from app.core.clock import Clock, SystemClock
from app.core.config import AppSettings
from app.core.logging import get_logger, structured_extra
from app.core.security import (
    BOOTSTRAP_ROLES,
    BOOTSTRAP_SCOPES,
    BOOTSTRAP_SUBJECT,
    TOKEN_TYPE_ACCESS,
)
from app.schemas.auth import AccessTokenClaims, AuthenticatedPrincipal, TokenResponse

logger = get_logger(__name__)

_REQUIRED_CLAIMS: Final[list[str]] = ["sub", "iss", "aud", "iat", "nbf", "exp", "jti", "token_type"]


class TokenService:
    """Create and validate HS256 bootstrap access tokens."""

    def __init__(
        self,
        settings: AppSettings,
        *,
        clock: Clock | None = None,
        jti_factory: Callable[[], str] | None = None,
    ) -> None:
        self._settings = settings
        self._clock = clock or SystemClock()
        self._jti_factory = jti_factory or (lambda: str(uuid4()))

    def create_bootstrap_access_token(self) -> TokenResponse:
        """Issue a fixed-identity bootstrap access token."""
        signing_key = self._require_signing_key()
        now = self._clock.now()
        iat = int(now.timestamp())
        nbf = iat
        exp = iat + self._settings.jwt_access_token_ttl_seconds
        jti = self._jti_factory()

        payload = {
            "sub": BOOTSTRAP_SUBJECT,
            "iss": self._settings.jwt_issuer,
            "aud": self._settings.jwt_audience,
            "iat": iat,
            "nbf": nbf,
            "exp": exp,
            "jti": jti,
            "token_type": TOKEN_TYPE_ACCESS,
            "roles": list(BOOTSTRAP_ROLES),
            "scopes": list(BOOTSTRAP_SCOPES),
            "environment": self._settings.environment.value,
        }
        token = jwt.encode(
            payload,
            signing_key,
            algorithm=self._settings.jwt_algorithm,
        )
        logger.info(
            "bootstrap access token issued",
            extra=structured_extra(
                event="auth.token.issued",
                source="token_service",
                auth_result="issued",
            ),
        )
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=self._settings.jwt_access_token_ttl_seconds,
        )

    def decode_access_token(self, token: str) -> AccessTokenClaims:
        """Decode and validate an access token; never log the raw token."""
        signing_key = self._require_signing_key()
        try:
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=[self._settings.jwt_algorithm],
                audience=self._settings.jwt_audience,
                issuer=self._settings.jwt_issuer,
                options={
                    "require": _REQUIRED_CLAIMS,
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": True,
                },
            )
        except ExpiredSignatureError as exc:
            raise EXPIRED_TOKEN from exc
        except InvalidIssuerError as exc:
            raise INVALID_ISSUER from exc
        except InvalidAudienceError as exc:
            raise INVALID_AUDIENCE from exc
        except (
            InvalidSignatureError,
            DecodeError,
            ImmatureSignatureError,
            InvalidIssuedAtError,
            MissingRequiredClaimError,
            InvalidTokenError,
        ) as exc:
            raise INVALID_TOKEN from exc

        try:
            if payload.get("token_type") != TOKEN_TYPE_ACCESS:
                raise INVALID_TOKEN_TYPE
            claims = AccessTokenClaims.model_validate(payload)
        except AuthError:
            raise
        except Exception as exc:
            raise INVALID_TOKEN from exc

        logger.info(
            "access token validated",
            extra=structured_extra(
                event="auth.token.validated",
                source="token_service",
                auth_result="validated",
            ),
        )
        return claims

    def principal_from_claims(self, claims: AccessTokenClaims) -> AuthenticatedPrincipal:
        """Convert validated claims into an immutable principal."""
        return AuthenticatedPrincipal(
            subject=claims.sub,
            roles=tuple(claims.roles),
            scopes=tuple(claims.scopes),
            token_id=claims.jti,
            issuer=claims.iss,
            audience=claims.aud,
        )

    def authenticate(self, token: str) -> AuthenticatedPrincipal:
        """Validate token and return principal."""
        claims = self.decode_access_token(token)
        return self.principal_from_claims(claims)

    def _require_signing_key(self) -> str:
        secret = self._settings.secrets.bootstrap_jwt_signing_key
        if secret is None:
            raise AuthError(
                code="auth.invalid_token",
                message="Authentication credentials are invalid.",
            )
        return secret.get_secret_value()
