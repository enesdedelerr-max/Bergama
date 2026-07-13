"""Unit tests for AppEnvironment."""

from __future__ import annotations

import pytest
from app.core.config import AppSettings
from app.core.environment import AppEnvironment
from pydantic import ValidationError


def test_environment_values_are_lowercase() -> None:
    assert AppEnvironment.LOCAL.value == "local"
    assert AppEnvironment.TEST.value == "test"
    assert AppEnvironment.STAGING.value == "staging"
    assert AppEnvironment.PRODUCTION.value == "production"


def test_unknown_environment_fails_validation() -> None:
    with pytest.raises(ValidationError):
        AppSettings(environment="paper")


def test_environment_is_normalized_from_uppercase() -> None:
    from tests.conftest import make_production_secrets

    settings = AppSettings(
        environment="PRODUCTION",
        debug=False,
        log_level="INFO",
        secrets=make_production_secrets(),
    )
    assert settings.environment is AppEnvironment.PRODUCTION


def test_only_local_loads_dotenv_flag() -> None:
    assert AppEnvironment.LOCAL.loads_dotenv is True
    assert AppEnvironment.TEST.loads_dotenv is False
    assert AppEnvironment.STAGING.loads_dotenv is False
    assert AppEnvironment.PRODUCTION.loads_dotenv is False
