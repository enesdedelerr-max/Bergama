"""Legacy #401 compatibility with #406 SDK introduction."""

from __future__ import annotations

import pytest
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.core.secrets import SecretSettings
from app.core.strategy_sdk_settings import StrategySdkRuntimeSettings
from app.core.strategy_settings import StrategySettings
from tests.conftest import VALID_PROD_JWT_SECRET
from tests.support.market_data_fixtures import make_bar
from tests.support.strategy_helpers import (
    noop_config,
    quality_assessment,
    strategy_engine,
    strategy_identity,
)


def _settings(**overrides: object) -> AppSettings:
    base: dict[str, object] = {
        "environment": AppEnvironment.TEST,
        "bootstrap_auth_enabled": True,
        "secrets": SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
    }
    base.update(overrides)
    return AppSettings(**base)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_legacy_runtime_remains_default_and_unchanged() -> None:
    engine, port = strategy_engine()
    session = engine.create_session(
        run_id="run-1",
        session_id="session-1",
        strategies=((strategy_identity(), noop_config()),),
    )
    event = make_bar()
    first = await session.evaluate(event, quality_assessment=quality_assessment(event))
    second = await session.evaluate(event, quality_assessment=quality_assessment(event))
    assert len(first) == 1
    assert second == ()
    assert len(port.decisions) == 1


def test_strategy_sdk_runtime_disabled_by_default_in_container() -> None:
    container = build_container(_settings())
    assert container.strategy_sdk_runtime_engine is None


def test_strategy_sdk_runtime_requires_explicit_enablement() -> None:
    settings = _settings(
        strategy_sdk=StrategySdkRuntimeSettings(enabled=True),
        strategy=StrategySettings(enabled=False),
    )
    container = build_container(settings)
    assert container.strategy_sdk_runtime_engine is not None
    assert container.strategy_engine is None
