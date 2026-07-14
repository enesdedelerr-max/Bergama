"""Unit tests for explicit container providers."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.clock import FixedClock, FixedJtiGenerator
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.core.providers import (
    provide_clock,
    provide_jti_generator,
    provide_settings,
    provide_token_service,
)
from app.core.secrets import SecretSettings
from app.services.token_service import TokenService
from tests.conftest import VALID_PROD_JWT_SECRET


def _settings() -> AppSettings:
    return AppSettings(
        environment=AppEnvironment.TEST,
        debug=False,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
    )


def test_providers_return_exact_owned_instances() -> None:
    settings = _settings()
    clock = FixedClock(datetime.now(UTC).replace(microsecond=0))
    jti = FixedJtiGenerator("provider-jti")
    token = TokenService(settings, clock=clock, jti_factory=jti)
    container = build_container(
        settings,
        clock=clock,
        jti_generator=jti,
        token_service=token,
    )
    assert provide_settings(container) is settings
    assert provide_clock(container) is clock
    assert provide_jti_generator(container) is jti
    assert provide_token_service(container) is token
    assert provide_token_service(container) is container.token_service
