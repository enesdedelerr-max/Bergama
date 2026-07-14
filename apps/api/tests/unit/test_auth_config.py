"""Unit tests for auth-related configuration policy."""

from __future__ import annotations

import pytest
from app.core.config import AppSettings
from app.core.environment import AppEnvironment
from app.core.secrets import SecretSettings
from pydantic import ValidationError
from tests.conftest import VALID_PROD_JWT_SECRET, make_production_secrets


def test_local_defaults_bootstrap_auth_enabled_requires_signing_key() -> None:
    with pytest.raises(ValidationError, match="BOOTSTRAP_JWT_SIGNING_KEY"):
        AppSettings(environment=AppEnvironment.LOCAL, bootstrap_auth_enabled=True)


def test_local_bootstrap_with_signing_key_passes() -> None:
    settings = AppSettings(
        environment=AppEnvironment.LOCAL,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
    )
    assert settings.bootstrap_auth_enabled is True
    assert settings.jwt_algorithm == "HS256"


def test_production_rejects_bootstrap_auth_enabled() -> None:
    with pytest.raises(ValidationError, match="BOOTSTRAP_AUTH_ENABLED"):
        AppSettings(
            environment=AppEnvironment.PRODUCTION,
            debug=False,
            bootstrap_auth_enabled=True,
            secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        )


def test_staging_rejects_bootstrap_auth_enabled() -> None:
    with pytest.raises(ValidationError, match="BOOTSTRAP_AUTH_ENABLED"):
        AppSettings(
            environment=AppEnvironment.STAGING,
            debug=False,
            bootstrap_auth_enabled=True,
            secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        )


def test_disabled_bootstrap_does_not_require_signing_key() -> None:
    settings = AppSettings(
        environment=AppEnvironment.PRODUCTION,
        debug=False,
        bootstrap_auth_enabled=False,
    )
    assert settings.bootstrap_auth_enabled is False
    assert settings.secrets.bootstrap_jwt_signing_key is None
    assert settings.secrets.app_secret_key is None


def test_unused_app_secret_not_required() -> None:
    settings = AppSettings(
        environment=AppEnvironment.STAGING,
        debug=False,
        bootstrap_auth_enabled=False,
        secrets=SecretSettings(bootstrap_jwt_signing_key=None, app_secret_key=None),
    )
    assert settings.secrets.app_secret_key is None


def test_production_default_disables_bootstrap() -> None:
    settings = AppSettings(environment=AppEnvironment.PRODUCTION, debug=False)
    assert settings.bootstrap_auth_enabled is False


def test_make_production_secrets_still_valid_when_provided() -> None:
    settings = AppSettings(
        environment=AppEnvironment.STAGING,
        debug=False,
        secrets=make_production_secrets(),
    )
    assert settings.secrets.app_secret_key is not None
