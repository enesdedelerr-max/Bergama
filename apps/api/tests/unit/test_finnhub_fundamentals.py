"""Offline Finnhub fundamentals/reference connector tests (Issue #304A)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import httpx
import pytest
from app.core.clock import FixedClock
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.core.finnhub_settings import FinnhubSettings
from app.core.secrets import SecretSettings
from app.infrastructure.finnhub.errors import (
    FinnhubAuthenticationFailedError,
    FinnhubConnectionFailedError,
    FinnhubForbiddenError,
    FinnhubInvalidRequestError,
    FinnhubInvalidResponseError,
    FinnhubMappingFailedError,
    FinnhubNotFoundError,
    FinnhubProviderError,
    FinnhubTimeoutError,
)
from app.infrastructure.finnhub.fundamentals import (
    FinnhubFundamentalsConnector,
    FundamentalsRequest,
)
from app.infrastructure.finnhub.http import FinnhubHttpClient
from app.infrastructure.finnhub.mapper import SUPPORTED_METRICS, map_fundamental_events
from app.infrastructure.finnhub.reference import FinnhubReferenceConnector, ReferenceRequest
from app.infrastructure.finnhub.schemas import FinnhubBasicFinancials
from app.market_data.enums import AssetClass
from app.market_data.identity import InstrumentId
from app.market_data.keys import build_deduplication_key, build_idempotency_key
from app.market_data.serialization import market_event_to_envelope, market_event_to_payload
from pydantic import SecretStr, ValidationError
from tests.conftest import VALID_PROD_JWT_SECRET

API_KEY = "test-finnhub-key-value"
BASE = "https://finnhub.io/api/v1"
OBSERVED = datetime(2024, 6, 15, 12, 0, tzinfo=UTC)


def _instrument() -> InstrumentId:
    return InstrumentId(
        instrument_key="bergama:equity:us:aapl",
        asset_class=AssetClass.EQUITY,
        local_symbol="AAPL",
        symbol_effective_from=datetime(2020, 1, 1, tzinfo=UTC),
    )


def _settings(**overrides: object) -> FinnhubSettings:
    base: dict[str, object] = {
        "enabled": True,
        "api_key": SecretStr(API_KEY),
        "base_url": BASE,
        "max_retries": 3,
        "retry_initial_delay_seconds": 0.01,
        "retry_max_delay_seconds": 0.05,
        "retry_after_max_seconds": 1.0,
    }
    base.update(overrides)
    return FinnhubSettings(**base)


class _Sleeper:
    def __init__(self) -> None:
        self.delays: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


def test_settings_disabled_by_default() -> None:
    settings = FinnhubSettings()
    assert settings.enabled is False
    assert settings.api_key is None


def test_api_key_required_when_enabled_and_redacted() -> None:
    with pytest.raises(ValidationError, match="API_KEY"):
        FinnhubSettings(enabled=True)
    configured = _settings()
    summary = configured.safe_summary()
    assert summary["api_key_configured"] is True
    assert API_KEY not in str(summary)
    assert API_KEY not in repr(configured)


@pytest.mark.asyncio
async def test_profile_and_fundamentals_happy_path(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("X-Finnhub-Token")
        assert "token" not in str(request.url).lower()
        if request.url.path.endswith("/stock/profile2"):
            return httpx.Response(
                200,
                headers={"X-Request-Id": "req-profile-1"},
                json={
                    "country": "US",
                    "currency": "USD",
                    "exchange": "NASDAQ NMS - GLOBAL MARKET",
                    "name": "Apple Inc",
                    "ticker": "AAPL",
                    "ipo": "1980-12-12",
                    "marketCapitalization": 2_500_000,
                    "shareOutstanding": 15_000,
                    "finnhubIndustry": "Technology",
                    "phone": "14089961010",
                    "weburl": "https://www.apple.com/",
                    "logo": "https://static.example/logo.png",
                },
            )
        if request.url.path.endswith("/stock/metric"):
            return httpx.Response(
                200,
                headers={"X-Request-Id": "req-metric-1"},
                json={
                    "symbol": "AAPL",
                    "metricType": "all",
                    "metric": {
                        "peTTM": 28.5,
                        "pbAnnual": 40.1,
                        "roeTTM": 147.2,
                        "currentRatioAnnual": 1.07,
                        "weirdUnknownMetric": 99.0,
                        "marketCapitalization": None,
                        "epsTTM": 6.42,
                        "unsupportedNoise": "x",
                    },
                    "series": {"annual": {"eps": [{"period": "2023", "v": 1}]}},
                },
            )
        raise AssertionError(f"unexpected {request.url}")

    transport = httpx.MockTransport(handler)
    http = FinnhubHttpClient(_settings(), transport=transport, sleeper=_Sleeper())
    clock = FixedClock(OBSERVED)
    ref = FinnhubReferenceConnector(http, clock=clock)
    fund = FinnhubFundamentalsConnector(http, clock=clock)
    try:
        reference = await ref.fetch_reference(
            ReferenceRequest(symbol="aapl", instrument=_instrument(), currency="USD")
        )
        fundamentals = await fund.fetch_fundamentals(
            FundamentalsRequest(symbol="AAPL", instrument=_instrument(), currency="USD")
        )
    finally:
        await http.aclose()

    assert captured["auth"] == API_KEY
    assert API_KEY not in caplog.text
    assert reference.name == "Apple Inc"
    assert reference.isin is None
    assert reference.cusip is None
    assert reference.exchange_mic is None
    assert reference.currency == "USD"
    assert reference.attributes["listed_exchange_text"].startswith("NASDAQ")
    assert reference.attributes["provider_currency"] == "USD"
    assert reference.attributes["finnhub_industry"] == "Technology"
    assert "logo" not in reference.attributes
    assert reference.source.provider == "finnhub"
    assert reference.source.source_symbol == "AAPL"
    assert reference.source.extras["endpoint"] == "stock/profile2"
    assert reference.source.extras["http_request_id"] == "req-profile-1"
    assert reference.occurred_at == OBSERVED == reference.ingested_at

    codes = [e.metric_code for e in fundamentals.events]
    assert codes == sorted(codes)
    assert "peTTM" in codes
    assert "weirdUnknownMetric" not in codes
    assert "unsupportedNoise" not in codes
    assert any("unsupported metric ignored" in r.getMessage() for r in caplog.records)
    assert "99.0" not in caplog.text
    pe = next(e for e in fundamentals.events if e.metric_code == "peTTM")
    assert pe.period == "ttm"
    assert pe.unit == "ratio"
    assert pe.value == Decimal("28.5")
    assert pe.instrument.instrument_key == "bergama:equity:us:aapl"
    assert pe.source.extras["endpoint"] == "stock/metric"
    assert pe.source.extras["http_request_id"] == "req-metric-1"
    assert all(e.occurred_at == OBSERVED for e in fundamentals.events)

    assert build_idempotency_key(reference)
    assert build_deduplication_key(pe)
    payload = market_event_to_payload(pe)
    assert payload["value"] == "28.5"
    env = market_event_to_envelope(reference)
    assert env.occurred_at == OBSERVED


@pytest.mark.asyncio
async def test_empty_profile_fails_closed() -> None:
    transport = httpx.MockTransport(lambda _r: httpx.Response(200, json={}))
    http = FinnhubHttpClient(_settings(), transport=transport, sleeper=_Sleeper())
    try:
        with pytest.raises(FinnhubNotFoundError):
            await FinnhubReferenceConnector(http, clock=FixedClock(OBSERVED)).fetch_reference(
                ReferenceRequest(symbol="ZZZZ", instrument=_instrument())
            )
    finally:
        await http.aclose()


def test_nan_infinity_invalid_supported_metric_and_currency_skip() -> None:
    clock_time = OBSERVED
    for bad in ("NaN", "Infinity", "-Infinity"):
        payload = FinnhubBasicFinancials.model_validate(
            {"symbol": "AAPL", "metric": {"peTTM": bad}}
        )
        with pytest.raises(FinnhubMappingFailedError):
            map_fundamental_events(
                payload,
                instrument=_instrument(),
                symbol="AAPL",
                observed_at=clock_time,
                request_id=None,
            )
    with_currency = map_fundamental_events(
        FinnhubBasicFinancials.model_validate(
            {"symbol": "AAPL", "metric": {"marketCapitalization": "1000", "peTTM": 10}}
        ),
        instrument=_instrument(),
        symbol="AAPL",
        observed_at=clock_time,
        request_id=None,
        caller_currency=None,
    )
    assert [e.metric_code for e in with_currency] == ["peTTM"]
    monetary = map_fundamental_events(
        FinnhubBasicFinancials.model_validate(
            {"symbol": "AAPL", "metric": {"marketCapitalization": "1000"}}
        ),
        instrument=_instrument(),
        symbol="AAPL",
        observed_at=clock_time,
        request_id=None,
        caller_currency="USD",
    )
    assert len(monetary) == 1
    assert monetary[0].unit == "currency"
    assert monetary[0].currency == "USD"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "exc"),
    [
        (400, FinnhubInvalidRequestError),
        (401, FinnhubAuthenticationFailedError),
        (403, FinnhubForbiddenError),
        (404, FinnhubNotFoundError),
    ],
)
async def test_client_errors_no_retry(status: int, exc: type[Exception]) -> None:
    calls = {"n": 0}
    sleeper = _Sleeper()

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(status, json={"error": "x"})

    http = FinnhubHttpClient(_settings(), transport=httpx.MockTransport(handler), sleeper=sleeper)
    try:
        with pytest.raises(exc):
            await FinnhubReferenceConnector(http, clock=FixedClock(OBSERVED)).fetch_reference(
                ReferenceRequest(symbol="AAPL", instrument=_instrument())
            )
    finally:
        await http.aclose()
    assert calls["n"] == 1
    assert sleeper.delays == []


@pytest.mark.asyncio
async def test_429_and_5xx_retry_then_success() -> None:
    state = {"n": 0}
    sleeper = _Sleeper()

    def handler(_request: httpx.Request) -> httpx.Response:
        state["n"] += 1
        if state["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "0.5"}, json={})
        if state["n"] == 2:
            return httpx.Response(503, json={})
        return httpx.Response(
            200,
            json={"name": "Apple Inc", "ticker": "AAPL", "country": "US"},
        )

    http = FinnhubHttpClient(_settings(), transport=httpx.MockTransport(handler), sleeper=sleeper)
    try:
        event = await FinnhubReferenceConnector(http, clock=FixedClock(OBSERVED)).fetch_reference(
            ReferenceRequest(symbol="AAPL", instrument=_instrument())
        )
    finally:
        await http.aclose()
    assert event.name == "Apple Inc"
    assert sleeper.delays[0] == 0.5
    assert len(sleeper.delays) == 2


@pytest.mark.asyncio
async def test_retry_exhaustion_timeout_connection_malformed() -> None:
    sleeper = _Sleeper()

    def always_500(_r: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={})

    http = FinnhubHttpClient(
        _settings(max_retries=2),
        transport=httpx.MockTransport(always_500),
        sleeper=sleeper,
    )
    try:
        with pytest.raises(FinnhubProviderError):
            await FinnhubReferenceConnector(http, clock=FixedClock(OBSERVED)).fetch_reference(
                ReferenceRequest(symbol="AAPL", instrument=_instrument())
            )
    finally:
        await http.aclose()

    def timeout(_r: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout")

    http = FinnhubHttpClient(
        _settings(max_retries=1),
        transport=httpx.MockTransport(timeout),
        sleeper=_Sleeper(),
    )
    try:
        with pytest.raises(FinnhubTimeoutError):
            await FinnhubReferenceConnector(http, clock=FixedClock(OBSERVED)).fetch_reference(
                ReferenceRequest(symbol="AAPL", instrument=_instrument())
            )
    finally:
        await http.aclose()

    def conn(_r: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    http = FinnhubHttpClient(
        _settings(max_retries=1),
        transport=httpx.MockTransport(conn),
        sleeper=_Sleeper(),
    )
    try:
        with pytest.raises(FinnhubConnectionFailedError):
            await FinnhubFundamentalsConnector(http, clock=FixedClock(OBSERVED)).fetch_fundamentals(
                FundamentalsRequest(symbol="AAPL", instrument=_instrument())
            )
    finally:
        await http.aclose()

    http = FinnhubHttpClient(
        _settings(),
        transport=httpx.MockTransport(lambda _r: httpx.Response(200, json=["not-object"])),
        sleeper=_Sleeper(),
    )
    try:
        with pytest.raises(FinnhubInvalidResponseError):
            await FinnhubReferenceConnector(http, clock=FixedClock(OBSERVED)).fetch_reference(
                ReferenceRequest(symbol="AAPL", instrument=_instrument())
            )
    finally:
        await http.aclose()


@pytest.mark.asyncio
async def test_container_disabled_and_isolation() -> None:
    disabled = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        finnhub=FinnhubSettings(enabled=False),
    )
    c0 = build_container(disabled)
    assert c0.finnhub_http is None
    assert c0.finnhub_reference is None
    assert c0.finnhub_fundamentals is None

    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        finnhub=_settings(),
    )
    t = httpx.MockTransport(lambda _r: httpx.Response(200, json={"ticker": "AAPL", "name": "A"}))
    h1 = FinnhubHttpClient(settings.finnhub, transport=t, sleeper=_Sleeper())
    h2 = FinnhubHttpClient(settings.finnhub, transport=t, sleeper=_Sleeper())
    c1 = build_container(settings, finnhub_http=h1)
    c2 = build_container(settings, finnhub_http=h2)
    assert c1.finnhub_http is h1
    assert c2.finnhub_http is h2
    assert c1.finnhub_http is not c2.finnhub_http
    await c1.aclose()
    await c2.aclose()


def test_supported_metrics_closed_set() -> None:
    assert "peTTM" in SUPPORTED_METRICS
    assert "series" not in SUPPORTED_METRICS
