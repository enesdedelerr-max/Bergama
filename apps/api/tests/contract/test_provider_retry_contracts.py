"""Cross-provider retry taxonomy contracts (#304E)."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest
from app.core.benzinga_settings import BenzingaSettings
from app.core.finnhub_settings import FinnhubSettings
from app.core.fred_settings import FredSettings
from app.core.polygon_settings import PolygonSettings
from app.core.sec_settings import SecSettings
from app.infrastructure.benzinga.errors import (
    BenzingaEntitlementRequiredError,
    BenzingaRateLimitedError,
)
from app.infrastructure.benzinga.http import BenzingaHttpClient
from app.infrastructure.benzinga.news import BenzingaNewsConnector, NewsRequest
from app.infrastructure.finnhub.errors import (
    FinnhubAuthenticationFailedError,
    FinnhubForbiddenError,
)
from app.infrastructure.finnhub.fundamentals import (
    FinnhubFundamentalsConnector,
    FundamentalsRequest,
)
from app.infrastructure.finnhub.http import FinnhubHttpClient
from app.infrastructure.fred.errors import FredAuthenticationFailedError, FredInvalidRequestError
from app.infrastructure.fred.http import FredHttpClient
from app.infrastructure.fred.series import FredSeriesConnector, SeriesRequest
from app.infrastructure.polygon.errors import (
    PolygonAuthenticationFailedError,
    PolygonProviderError,
)
from app.infrastructure.polygon.historical import HistoricalBarsRequest, PolygonHistoricalConnector
from app.infrastructure.polygon.http import PolygonHttpClient
from app.infrastructure.sec.errors import SecForbiddenError
from app.infrastructure.sec.http import SecHttpClient
from app.infrastructure.sec.submissions import SecSubmissionsConnector, SubmissionsRequest
from pydantic import SecretStr
from tests.support.provider_contracts.clocks import observed_clock
from tests.support.provider_contracts.identities import equity_instrument, news_anchor_instrument

KEY = "contract-retry-secret-abcdefgh"


class _Sleeper:
    def __init__(self) -> None:
        self.delays: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


@pytest.mark.asyncio
async def test_polygon_retries_5xx_not_401() -> None:
    sleeper = _Sleeper()
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(500, json={})

    http = PolygonHttpClient(
        PolygonSettings(
            enabled=True,
            api_key=SecretStr(KEY),
            max_retries=2,
            retry_initial_delay_seconds=0.01,
            retry_max_delay_seconds=0.02,
            retry_after_max_seconds=1.0,
        ),
        transport=httpx.MockTransport(handler),
        sleeper=sleeper,
    )
    with pytest.raises(PolygonProviderError):
        await http.get("/v2/aggs/ticker/AAPL/range/1/day/2024-01-01/2024-01-02")
    await http.aclose()
    assert calls["n"] == 2
    assert sleeper.delays

    auth_calls = {"n": 0}

    def auth(_request: httpx.Request) -> httpx.Response:
        auth_calls["n"] += 1
        return httpx.Response(401, json={})

    sleeper2 = _Sleeper()
    http2 = PolygonHttpClient(
        PolygonSettings(enabled=True, api_key=SecretStr(KEY), max_retries=3),
        transport=httpx.MockTransport(auth),
        sleeper=sleeper2,
    )
    connector = PolygonHistoricalConnector(http2, clock=observed_clock())
    with pytest.raises(PolygonAuthenticationFailedError):
        await connector.fetch_bars(
            HistoricalBarsRequest(
                symbol="AAPL",
                instrument=equity_instrument(),
                currency="USD",
                timespan="day",
                multiplier=1,
                start=datetime(2024, 1, 1, tzinfo=UTC),
                end=datetime(2024, 1, 2, tzinfo=UTC),
            )
        )
    await http2.aclose()
    assert auth_calls["n"] == 1
    assert sleeper2.delays == []


@pytest.mark.asyncio
async def test_benzinga_429_exhaustion_is_rate_limited() -> None:
    sleeper = _Sleeper()
    n = {"c": 0}

    def limited(_request: httpx.Request) -> httpx.Response:
        n["c"] += 1
        return httpx.Response(429, headers={"Retry-After": "0.01"}, json={})

    http = BenzingaHttpClient(
        BenzingaSettings(
            enabled=True,
            api_key=SecretStr(KEY),
            max_retries=1,
            retry_initial_delay_seconds=0.01,
            retry_max_delay_seconds=0.02,
            max_retry_after_seconds=1.0,
        ),
        transport=httpx.MockTransport(limited),
        sleeper=sleeper,
    )
    with pytest.raises(BenzingaRateLimitedError):
        await http.get("/api/v2/news", params={"page": 0})
    await http.aclose()
    assert n["c"] == 1


@pytest.mark.asyncio
async def test_auth_and_entitlement_mappings_are_not_retried() -> None:
    fh = FinnhubHttpClient(
        FinnhubSettings(enabled=True, api_key=SecretStr(KEY), max_retries=3),
        transport=httpx.MockTransport(lambda _r: httpx.Response(401, json={})),
        sleeper=_Sleeper(),
    )
    with pytest.raises(FinnhubAuthenticationFailedError):
        await FinnhubFundamentalsConnector(fh, clock=observed_clock()).fetch_fundamentals(
            FundamentalsRequest(symbol="AAPL", instrument=equity_instrument(), currency="USD")
        )
    await fh.aclose()

    fh2 = FinnhubHttpClient(
        FinnhubSettings(enabled=True, api_key=SecretStr(KEY), max_retries=3),
        transport=httpx.MockTransport(lambda _r: httpx.Response(403, json={})),
        sleeper=_Sleeper(),
    )
    with pytest.raises(FinnhubForbiddenError):
        await FinnhubFundamentalsConnector(fh2, clock=observed_clock()).fetch_fundamentals(
            FundamentalsRequest(symbol="AAPL", instrument=equity_instrument(), currency="USD")
        )
    await fh2.aclose()

    fr = FredHttpClient(
        FredSettings(enabled=True, api_key=SecretStr(KEY), max_retries=3),
        transport=httpx.MockTransport(lambda _r: httpx.Response(401, json={})),
        sleeper=_Sleeper(),
    )
    with pytest.raises(FredAuthenticationFailedError):
        await FredSeriesConnector(fr, clock=observed_clock()).fetch_series(
            SeriesRequest(series_id="GDP")
        )
    await fr.aclose()

    sec_http = SecHttpClient(
        SecSettings(
            enabled=True,
            contact_email="contracts@bergama-trading.test",
            max_retries=3,
            min_request_interval_seconds=0.1,
        ),
        transport=httpx.MockTransport(lambda _r: httpx.Response(403, json={})),
        sleeper=_Sleeper(),
    )
    with pytest.raises(SecForbiddenError):
        await SecSubmissionsConnector(sec_http, clock=observed_clock()).fetch_submissions(
            SubmissionsRequest(cik="320193", instrument=equity_instrument(), max_filings=1)
        )
    await sec_http.aclose()

    bz = BenzingaHttpClient(
        BenzingaSettings(enabled=True, api_key=SecretStr(KEY), max_retries=3),
        transport=httpx.MockTransport(lambda _r: httpx.Response(403, json={})),
        sleeper=_Sleeper(),
    )
    with pytest.raises(BenzingaEntitlementRequiredError):
        await BenzingaNewsConnector(bz, clock=observed_clock()).fetch_news(
            NewsRequest(date="2024-01-01", anchor_instrument=news_anchor_instrument())
        )
    await bz.aclose()


@pytest.mark.asyncio
async def test_400_is_not_retried() -> None:
    sleeper = _Sleeper()
    calls = {"n": 0}

    def bad(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(400, json={})

    http = FredHttpClient(
        FredSettings(enabled=True, api_key=SecretStr(KEY), max_retries=3),
        transport=httpx.MockTransport(bad),
        sleeper=sleeper,
    )
    with pytest.raises(FredInvalidRequestError):
        await FredSeriesConnector(http, clock=observed_clock()).fetch_series(
            SeriesRequest(series_id="GDP")
        )
    await http.aclose()
    assert calls["n"] == 1
    assert sleeper.delays == []
