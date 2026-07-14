"""Offline FRED macro connector tests (Issue #304B)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pytest
from app.core.clock import FixedClock
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.core.fred_settings import FredSettings
from app.core.secrets import SecretSettings
from app.infrastructure.fred.errors import (
    FredAuthenticationFailedError,
    FredConnectionFailedError,
    FredForbiddenError,
    FredInvalidRequestError,
    FredInvalidResponseError,
    FredMappingFailedError,
    FredNotFoundError,
    FredPaginationLimitError,
    FredPaginationStateError,
    FredProviderError,
    FredTimeoutError,
)
from app.infrastructure.fred.http import FredHttpClient
from app.infrastructure.fred.mapper import map_observation_events, map_series_metadata
from app.infrastructure.fred.observations import (
    FredObservationsConnector,
    ObservationsRequest,
)
from app.infrastructure.fred.pagination import sanitize_url
from app.infrastructure.fred.schemas import FredObservation, FredSeries
from app.infrastructure.fred.series import FredSeriesConnector, SeriesRequest
from app.market_data.enums import AssetClass
from app.market_data.identity import InstrumentId
from app.market_data.keys import build_deduplication_key, build_idempotency_key
from app.market_data.serialization import market_event_to_envelope, market_event_to_payload
from pydantic import SecretStr, ValidationError
from tests.conftest import VALID_PROD_JWT_SECRET

API_KEY = "test-fred-key-value-abcdefghijklmnop"
BASE = "https://api.stlouisfed.org"
OBSERVED = datetime(2024, 6, 15, 12, 0, tzinfo=UTC)


def _instrument() -> InstrumentId:
    return InstrumentId(
        instrument_key="bergama:macro:us:gdp",
        asset_class=AssetClass.MACRO,
        local_symbol="GDP",
        symbol_effective_from=datetime(2020, 1, 1, tzinfo=UTC),
    )


def _settings(**overrides: object) -> FredSettings:
    base: dict[str, object] = {
        "enabled": True,
        "api_key": SecretStr(API_KEY),
        "base_url": BASE,
        "max_retries": 3,
        "retry_initial_delay_seconds": 0.01,
        "retry_max_delay_seconds": 0.05,
        "retry_after_max_seconds": 1.0,
        "max_pages": 5,
        "max_results_per_page": 2,
    }
    base.update(overrides)
    return FredSettings(**base)


class _Sleeper:
    def __init__(self) -> None:
        self.delays: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


def test_settings_disabled_by_default() -> None:
    settings = FredSettings()
    assert settings.enabled is False
    assert settings.api_key is None


def test_api_key_required_when_enabled_and_redacted() -> None:
    with pytest.raises(ValidationError, match="API_KEY"):
        FredSettings(enabled=True)
    configured = _settings()
    summary = configured.safe_summary()
    assert summary["api_key_configured"] is True
    assert API_KEY not in str(summary)
    assert API_KEY not in repr(configured)


def test_sanitize_url_redacts_api_key() -> None:
    url = f"{BASE}/fred/series?series_id=GDP&api_key={API_KEY}&file_type=json"
    cleaned = sanitize_url(url)
    assert API_KEY not in cleaned
    assert "api_key" not in cleaned.lower()
    assert "series_id=GDP" in cleaned


@pytest.mark.asyncio
async def test_series_and_observations_happy_path(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params.get("api_key") == API_KEY
        assert request.url.params.get("file_type") == "json"
        calls.append(str(request.url.path))
        if request.url.path.endswith("/fred/series"):
            return httpx.Response(
                200,
                json={
                    "realtime_start": "2024-06-15",
                    "realtime_end": "2024-06-15",
                    "seriess": [
                        {
                            "id": "GDP",
                            "title": "Gross Domestic Product",
                            "frequency": "Quarterly",
                            "frequency_short": "Q",
                            "units": "Billions of Dollars",
                            "units_short": "Bil. of $",
                            "seasonal_adjustment": "Seasonally Adjusted Annual Rate",
                            "seasonal_adjustment_short": "SAAR",
                            "observation_start": "1947-01-01",
                            "observation_end": "2024-01-01",
                            "last_updated": "2024-04-25 07:53:02-05",
                            "notes": "BEA Account Code: A191RC",
                        }
                    ],
                },
            )
        if request.url.path.endswith("/fred/series/observations"):
            offset = int(request.url.params.get("offset", "0"))
            if offset == 0:
                return httpx.Response(
                    200,
                    json={
                        "count": 3,
                        "offset": 0,
                        "limit": 2,
                        "observations": [
                            {
                                "realtime_start": "2020-04-29",
                                "realtime_end": "2021-01-27",
                                "date": "2020-01-01",
                                "value": "21500.1",
                            },
                            {
                                "realtime_start": "2020-04-29",
                                "realtime_end": "2021-01-27",
                                "date": "2020-01-01",
                                "value": ".",
                            },
                        ],
                    },
                )
            return httpx.Response(
                200,
                json={
                    "count": 3,
                    "offset": 2,
                    "limit": 2,
                    "observations": [
                        {
                            "realtime_start": "2021-01-28",
                            "realtime_end": "9999-12-31",
                            "date": "2020-01-01",
                            "value": "21700.5",
                        }
                    ],
                },
            )
        raise AssertionError(f"unexpected {request.url}")

    transport = httpx.MockTransport(handler)
    http = FredHttpClient(_settings(), transport=transport, sleeper=_Sleeper())
    clock = FixedClock(OBSERVED)
    try:
        meta = await FredSeriesConnector(http, clock=clock).fetch_series(
            SeriesRequest(series_id="gdp")
        )
        result = await FredObservationsConnector(http, clock=clock).fetch_observations(
            ObservationsRequest(
                fred_series_id="GDP",
                series_id="US_GDP",
                instrument=_instrument(),
                series_meta=meta,
                observation_start="2020-01-01",
                observation_end="2020-12-31",
            )
        )
    finally:
        await http.aclose()

    assert API_KEY not in caplog.text
    assert meta.frequency == "quarterly"
    assert meta.title == "Gross Domestic Product"
    assert meta.units_raw == "Billions of Dollars"
    assert result.pages_fetched == 2
    assert result.skipped_missing == 1
    assert len(result.events) == 2
    assert all(e.series_id == "US_GDP" for e in result.events)
    assert all(e.source.source_symbol == "GDP" for e in result.events)
    assert all(e.unit is None for e in result.events)
    assert all(e.frequency == "quarterly" for e in result.events)
    assert result.events[0].value == Decimal("21500.1")
    assert result.events[0].occurred_at == datetime(2020, 1, 1, tzinfo=UTC)
    assert result.events[0].effective_at == datetime(2020, 1, 1, tzinfo=UTC)
    assert result.events[0].known_at == datetime(2020, 4, 29, tzinfo=UTC)
    assert result.events[1].known_at == datetime(2021, 1, 28, tzinfo=UTC)
    assert result.events[0].ingested_at == OBSERVED
    assert result.events[0].metadata["fred_units"].startswith("Billions")
    assert all(API_KEY not in ref for ref in result.endpoint_refs)

    keys = {build_idempotency_key(e) for e in result.events}
    assert len(keys) == 2
    dedup = {build_deduplication_key(e) for e in result.events}
    assert len(dedup) == 2
    payload = market_event_to_payload(result.events[0])
    assert payload["value"] == "21500.1"
    env = market_event_to_envelope(result.events[0])
    assert env.payload["series_id"] == "US_GDP"
    assert "missing observation value skipped" in caplog.text


def test_mapping_rejects_nan_and_preserves_unknown_frequency() -> None:
    with pytest.raises(FredMappingFailedError):
        map_observation_events(
            [
                FredObservation(
                    realtime_start="2020-04-29",
                    realtime_end="2020-04-29",
                    date="2020-01-01",
                    value="NaN",
                )
            ],
            instrument=_instrument(),
            canonical_series_id="US_GDP",
            fred_series_id="GDP",
            series_meta=None,
            ingested_at=OBSERVED,
        )
    meta = map_series_metadata(
        FredSeries(
            id="X",
            frequency="Biweekly",
            frequency_short="BW",
            units="Index",
        )
    )
    assert meta.frequency is None
    assert meta.frequency_raw == "BW"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "exc"),
    [
        (400, FredInvalidRequestError),
        (401, FredAuthenticationFailedError),
        (403, FredForbiddenError),
        (404, FredNotFoundError),
    ],
)
async def test_client_errors_no_retry(status: int, exc: type[Exception]) -> None:
    calls = {"n": 0}
    sleeper = _Sleeper()

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(status, json={"error_code": status})

    http = FredHttpClient(_settings(), transport=httpx.MockTransport(handler), sleeper=sleeper)
    try:
        with pytest.raises(exc):
            await FredSeriesConnector(http, clock=FixedClock(OBSERVED)).fetch_series(
                SeriesRequest(series_id="GDP")
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
            json={
                "seriess": [
                    {
                        "id": "GDP",
                        "title": "Gross Domestic Product",
                        "frequency_short": "Q",
                        "frequency": "Quarterly",
                    }
                ]
            },
        )

    http = FredHttpClient(_settings(), transport=httpx.MockTransport(handler), sleeper=sleeper)
    try:
        meta = await FredSeriesConnector(http, clock=FixedClock(OBSERVED)).fetch_series(
            SeriesRequest(series_id="GDP")
        )
    finally:
        await http.aclose()
    assert meta.fred_series_id == "GDP"
    assert sleeper.delays[0] == 0.5
    assert len(sleeper.delays) == 2


@pytest.mark.asyncio
async def test_retry_exhaustion_timeout_connection_malformed_pagination() -> None:
    sleeper = _Sleeper()
    http = FredHttpClient(
        _settings(max_retries=2),
        transport=httpx.MockTransport(lambda _r: httpx.Response(500, json={})),
        sleeper=sleeper,
    )
    try:
        with pytest.raises(FredProviderError):
            await FredSeriesConnector(http, clock=FixedClock(OBSERVED)).fetch_series(
                SeriesRequest(series_id="GDP")
            )
    finally:
        await http.aclose()

    def timeout(_r: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout")

    http = FredHttpClient(
        _settings(max_retries=1),
        transport=httpx.MockTransport(timeout),
        sleeper=_Sleeper(),
    )
    try:
        with pytest.raises(FredTimeoutError):
            await FredSeriesConnector(http, clock=FixedClock(OBSERVED)).fetch_series(
                SeriesRequest(series_id="GDP")
            )
    finally:
        await http.aclose()

    def conn(_r: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    http = FredHttpClient(
        _settings(max_retries=1),
        transport=httpx.MockTransport(conn),
        sleeper=_Sleeper(),
    )
    try:
        with pytest.raises(FredConnectionFailedError):
            await FredObservationsConnector(http, clock=FixedClock(OBSERVED)).fetch_observations(
                ObservationsRequest(
                    fred_series_id="GDP",
                    series_id="US_GDP",
                    instrument=_instrument(),
                )
            )
    finally:
        await http.aclose()

    http = FredHttpClient(
        _settings(),
        transport=httpx.MockTransport(lambda _r: httpx.Response(200, json=["bad"])),
        sleeper=_Sleeper(),
    )
    try:
        with pytest.raises(FredInvalidResponseError):
            await FredSeriesConnector(http, clock=FixedClock(OBSERVED)).fetch_series(
                SeriesRequest(series_id="GDP")
            )
    finally:
        await http.aclose()

    # Repeated offset via page limit / guard: max_pages=1 with count requiring more pages.
    offsets_seen: list[int] = []

    def paginate(request: httpx.Request) -> httpx.Response:
        offset = int(request.url.params.get("offset", "0"))
        offsets_seen.append(offset)
        return httpx.Response(
            200,
            json={
                "count": 10,
                "offset": offset,
                "limit": 2,
                "observations": [
                    {
                        "realtime_start": "2020-04-29",
                        "realtime_end": "2020-04-29",
                        "date": "2020-01-01",
                        "value": "1",
                    },
                    {
                        "realtime_start": "2020-07-30",
                        "realtime_end": "2020-07-30",
                        "date": "2020-04-01",
                        "value": "2",
                    },
                ],
            },
        )

    http = FredHttpClient(
        _settings(max_pages=1, max_results_per_page=2),
        transport=httpx.MockTransport(paginate),
        sleeper=_Sleeper(),
    )
    try:
        with pytest.raises(FredPaginationLimitError):
            await FredObservationsConnector(http, clock=FixedClock(OBSERVED)).fetch_observations(
                ObservationsRequest(
                    fred_series_id="GDP",
                    series_id="US_GDP",
                    instrument=_instrument(),
                )
            )
    finally:
        await http.aclose()


@pytest.mark.asyncio
async def test_inconsistent_offset_rejected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "count": 1,
                "offset": 99,
                "limit": 2,
                "observations": [
                    {
                        "realtime_start": "2020-04-29",
                        "realtime_end": "2020-04-29",
                        "date": "2020-01-01",
                        "value": "1",
                    }
                ],
            },
        )

    http = FredHttpClient(_settings(), transport=httpx.MockTransport(handler), sleeper=_Sleeper())
    try:
        with pytest.raises(FredInvalidResponseError, match="offset mismatch"):
            await FredObservationsConnector(http, clock=FixedClock(OBSERVED)).fetch_observations(
                ObservationsRequest(
                    fred_series_id="GDP",
                    series_id="US_GDP",
                    instrument=_instrument(),
                )
            )
    finally:
        await http.aclose()


@pytest.mark.asyncio
async def test_container_disabled_and_isolation() -> None:
    disabled = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        fred=FredSettings(enabled=False),
    )
    c0 = build_container(disabled)
    assert c0.fred_http is None
    assert c0.fred_series is None
    assert c0.fred_observations is None

    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        fred=_settings(),
    )
    t = httpx.MockTransport(lambda _r: httpx.Response(200, json={"seriess": [{"id": "GDP"}]}))
    h1 = FredHttpClient(settings.fred, transport=t, sleeper=_Sleeper())
    h2 = FredHttpClient(settings.fred, transport=t, sleeper=_Sleeper())
    c1 = build_container(settings, fred_http=h1)
    c2 = build_container(settings, fred_http=h2)
    assert c1.fred_http is h1
    assert c2.fred_http is h2
    assert c1.fred_http is not c2.fred_http
    await c1.aclose()
    await c2.aclose()


def test_pagination_state_error_on_repeat() -> None:
    from app.infrastructure.fred.pagination import OffsetPaginationGuard

    guard = OffsetPaginationGuard(max_pages=3)
    guard.begin_page(0)
    with pytest.raises(FredPaginationStateError):
        guard.begin_page(0)
