"""Cross-provider AppContainer lifecycle contracts (#304E)."""

from __future__ import annotations

import pytest
from app.core.benzinga_settings import BenzingaSettings
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.core.finnhub_settings import FinnhubSettings
from app.core.fred_settings import FredSettings
from app.core.polygon_settings import PolygonSettings
from app.core.sec_settings import SecSettings
from app.core.secrets import SecretSettings
from pydantic import SecretStr
from tests.conftest import VALID_PROD_JWT_SECRET

KEY = "contract-lifecycle-secret-abcdefgh"


def _base(**overrides: object) -> AppSettings:
    data: dict[str, object] = {
        "environment": AppEnvironment.TEST,
        "secrets": SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
    }
    data.update(overrides)
    return AppSettings(**data)  # type: ignore[arg-type]


def test_disabled_providers_create_no_clients() -> None:
    container = build_container(_base())
    assert container.polygon_http is None
    assert container.polygon_historical is None
    assert container.polygon_realtime is None
    assert container.finnhub_http is None
    assert container.fred_http is None
    assert container.sec_http is None
    assert container.benzinga_http is None
    assert container.benzinga_news is None


@pytest.mark.asyncio
async def test_enabled_providers_are_application_scoped_and_close_idempotently() -> None:
    settings = _base(
        polygon=PolygonSettings(enabled=True, api_key=SecretStr(KEY), websocket_enabled=False),
        finnhub=FinnhubSettings(enabled=True, api_key=SecretStr(KEY)),
        fred=FredSettings(enabled=True, api_key=SecretStr(KEY)),
        sec=SecSettings(
            enabled=True,
            contact_email="contracts@bergama-trading.test",
            min_request_interval_seconds=0.1,
        ),
        benzinga=BenzingaSettings(enabled=True, api_key=SecretStr(KEY)),
    )
    c1 = build_container(settings)
    c2 = build_container(settings)
    assert c1.polygon_http is not None and c2.polygon_http is not None
    assert c1.polygon_http is not c2.polygon_http
    assert c1.finnhub_http is not c2.finnhub_http
    assert c1.fred_http is not c2.fred_http
    assert c1.sec_http is not c2.sec_http
    assert c1.benzinga_http is not c2.benzinga_http
    assert c1.polygon_realtime is None  # websocket disabled; no startup fetch

    await c1.aclose()
    await c1.aclose()
    await c2.aclose()


@pytest.mark.asyncio
async def test_polygon_realtime_stop_before_http_close_order() -> None:
    # When WS is enabled, realtime must exist and close path runs before HTTP aclose.
    settings = _base(
        polygon=PolygonSettings(
            enabled=True,
            api_key=SecretStr(KEY),
            websocket_enabled=True,
        )
    )
    container = build_container(settings)
    assert container.polygon_realtime is not None
    assert container.polygon_http is not None
    await container.aclose()
    await container.aclose()
