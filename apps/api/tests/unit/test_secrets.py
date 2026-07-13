"""Unit tests for SecretSettings validation and redaction."""

from __future__ import annotations

import pytest
from app.core.secrets import MIN_CRYPTO_SECRET_LENGTH, SecretSettings
from pydantic import SecretStr, ValidationError
from tests.conftest import VALID_PROD_APP_SECRET, VALID_PROD_JWT_SECRET, make_production_secrets


def test_secretstr_repr_is_redacted() -> None:
    secrets = make_production_secrets()
    assert VALID_PROD_APP_SECRET not in repr(secrets)
    assert VALID_PROD_JWT_SECRET not in repr(secrets)
    assert "**********" in repr(secrets.app_secret_key)
    assert secrets.app_secret_key is not None
    assert secrets.app_secret_key.get_secret_value() == VALID_PROD_APP_SECRET


def test_safe_summary_excludes_secret_values() -> None:
    secrets = make_production_secrets()
    summary = secrets.safe_summary()
    assert summary == {
        "app_secret_key_configured": True,
        "bootstrap_jwt_signing_key_configured": True,
    }
    assert VALID_PROD_APP_SECRET not in str(summary)


def test_whitespace_secret_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        SecretSettings(app_secret_key="  leading-and-trailing-space-value-0001  ")
    assert "leading or trailing whitespace" in str(exc_info.value)
    assert "leading-and-trailing-space-value-0001" not in str(exc_info.value)


def test_empty_string_becomes_none() -> None:
    secrets = SecretSettings(app_secret_key="", bootstrap_jwt_signing_key="")
    assert secrets.app_secret_key is None
    assert secrets.bootstrap_jwt_signing_key is None


def test_bootstrap_signing_key_missing_fails_when_validated() -> None:
    secrets = SecretSettings()
    with pytest.raises(ValueError, match="required"):
        secrets.validate_bootstrap_signing_key()


def test_bootstrap_placeholder_fails() -> None:
    secrets = SecretSettings(bootstrap_jwt_signing_key="changeme")
    with pytest.raises(ValueError, match="placeholder") as exc_info:
        secrets.validate_bootstrap_signing_key()
    assert "changeme" not in str(exc_info.value)


def test_bootstrap_weak_length_fails() -> None:
    short = "x" * (MIN_CRYPTO_SECRET_LENGTH - 1)
    secrets = SecretSettings(bootstrap_jwt_signing_key=short)
    with pytest.raises(ValueError, match="at least") as exc_info:
        secrets.validate_bootstrap_signing_key()
    assert short not in str(exc_info.value)


def test_bootstrap_valid_passes() -> None:
    secrets = SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET)
    secrets.validate_bootstrap_signing_key()


def test_app_secret_optional() -> None:
    secrets = SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET)
    assert secrets.app_secret_key is None


def test_explicit_access_pattern() -> None:
    secrets = SecretSettings(bootstrap_jwt_signing_key=SecretStr(VALID_PROD_JWT_SECRET))
    assert secrets.bootstrap_jwt_signing_key is not None
    assert secrets.bootstrap_jwt_signing_key.get_secret_value() == VALID_PROD_JWT_SECRET
