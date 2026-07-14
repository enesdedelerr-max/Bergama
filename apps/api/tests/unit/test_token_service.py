"""Unit tests for JWT token service."""

from __future__ import annotations

from datetime import UTC, datetime

import jwt
import pytest
from app.auth.errors import AuthError
from app.core.clock import FixedClock
from app.core.config import AppSettings
from app.core.environment import AppEnvironment
from app.core.secrets import SecretSettings
from app.core.security import BOOTSTRAP_SUBJECT, TOKEN_TYPE_ACCESS
from app.services.token_service import TokenService
from tests.conftest import VALID_PROD_JWT_SECRET


def _auth_settings(**overrides: object) -> AppSettings:
    base: dict[str, object] = {
        "environment": AppEnvironment.TEST,
        "debug": False,
        "bootstrap_auth_enabled": True,
        "jwt_issuer": "bergama-api",
        "jwt_audience": "bergama-api",
        "jwt_access_token_ttl_seconds": 900,
        "secrets": SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
    }
    base.update(overrides)
    return AppSettings(**base)  # type: ignore[arg-type]


def test_token_creation_contains_required_claims() -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    clock = FixedClock(now)
    service = TokenService(_auth_settings(), clock=clock, jti_factory=lambda: "jti-fixed-1")
    response = service.create_bootstrap_access_token()
    assert response.token_type == "bearer"
    assert response.expires_in == 900
    assert VALID_PROD_JWT_SECRET not in response.access_token

    claims = service.decode_access_token(response.access_token)
    assert claims.sub == BOOTSTRAP_SUBJECT
    assert claims.iss == "bergama-api"
    assert claims.aud == "bergama-api"
    assert claims.jti == "jti-fixed-1"
    assert claims.token_type == TOKEN_TYPE_ACCESS
    assert claims.roles == ["developer"]
    assert claims.scopes == ["api:read"]
    assert claims.iat == int(now.timestamp())
    assert claims.nbf == claims.iat
    assert claims.exp == claims.iat + 900


def test_invalid_signature_fails() -> None:
    service = TokenService(_auth_settings(), jti_factory=lambda: "jti-1")
    token = service.create_bootstrap_access_token().access_token
    other = TokenService(
        _auth_settings(
            secrets=SecretSettings(
                bootstrap_jwt_signing_key="other-valid-jwt-signing-key-value-0001"
            )
        )
    )
    with pytest.raises(AuthError) as exc_info:
        other.decode_access_token(token)
    assert exc_info.value.code == "auth.invalid_token"


def test_expired_token_fails() -> None:
    issued_at = FixedClock(datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC))
    service = TokenService(
        _auth_settings(jwt_access_token_ttl_seconds=60),
        clock=issued_at,
        jti_factory=lambda: "jti-exp",
    )
    token = service.create_bootstrap_access_token().access_token
    later = TokenService(
        _auth_settings(jwt_access_token_ttl_seconds=60),
        clock=FixedClock(datetime(2026, 1, 1, 12, 5, 0, tzinfo=UTC)),
    )
    with pytest.raises(AuthError) as exc_info:
        later.decode_access_token(token)
    assert exc_info.value.code == "auth.expired_token"


def test_wrong_issuer_fails() -> None:
    service = TokenService(_auth_settings(), jti_factory=lambda: "jti-iss")
    token = service.create_bootstrap_access_token().access_token
    verifier = TokenService(_auth_settings(jwt_issuer="other-issuer"), jti_factory=lambda: "x")
    with pytest.raises(AuthError) as exc_info:
        verifier.decode_access_token(token)
    assert exc_info.value.code == "auth.invalid_issuer"


def test_wrong_audience_fails() -> None:
    service = TokenService(_auth_settings(), jti_factory=lambda: "jti-aud")
    token = service.create_bootstrap_access_token().access_token
    verifier = TokenService(_auth_settings(jwt_audience="other-aud"), jti_factory=lambda: "x")
    with pytest.raises(AuthError) as exc_info:
        verifier.decode_access_token(token)
    assert exc_info.value.code == "auth.invalid_audience"


def test_wrong_algorithm_fails() -> None:
    settings = _auth_settings()
    # Craft a token with none algorithm rejected by decode algorithms list.
    forged = jwt.encode(
        {
            "sub": BOOTSTRAP_SUBJECT,
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "iat": 1,
            "nbf": 1,
            "exp": 9999999999,
            "jti": "jti-alg",
            "token_type": TOKEN_TYPE_ACCESS,
        },
        key="",
        algorithm="none",
    )
    service = TokenService(settings)
    with pytest.raises(AuthError) as exc_info:
        service.decode_access_token(forged)
    assert exc_info.value.code == "auth.invalid_token"


def test_wrong_token_type_fails() -> None:
    settings = _auth_settings()
    token = jwt.encode(
        {
            "sub": BOOTSTRAP_SUBJECT,
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "iat": 1_700_000_000,
            "nbf": 1_700_000_000,
            "exp": 1_800_000_000,
            "jti": "jti-type",
            "token_type": "refresh",
        },
        VALID_PROD_JWT_SECRET,
        algorithm="HS256",
    )
    service = TokenService(settings)
    with pytest.raises(AuthError) as exc_info:
        service.decode_access_token(token)
    assert exc_info.value.code == "auth.invalid_token_type"


def test_signing_secret_not_in_repr() -> None:
    settings = _auth_settings()
    assert VALID_PROD_JWT_SECRET not in repr(settings)
    assert VALID_PROD_JWT_SECRET not in repr(settings.secrets)
