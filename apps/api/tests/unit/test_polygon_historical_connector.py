"""Offline Polygon historical connector tests (httpx.MockTransport)."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from app.core.clock import FixedClock
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.core.polygon_settings import PolygonSettings
from app.core.secrets import SecretSettings
from app.infrastructure.polygon.errors import (
    PolygonAuthenticationFailedError,
    PolygonConnectionFailedError,
    PolygonForbiddenError,
    PolygonInvalidRequestError,
    PolygonInvalidResponseError,
    PolygonMappingFailedError,
    PolygonNotFoundError,
    PolygonPaginationLimitError,
    PolygonPaginationLoopError,
    PolygonProviderError,
    PolygonRateLimitedError,
    PolygonTimeoutError,
)
from app.infrastructure.polygon.historical import (
    HistoricalBarsRequest,
    PolygonHistoricalConnector,
    PolygonTimespan,
)
from app.infrastructure.polygon.http import PolygonHttpClient
from app.infrastructure.polygon.mapper import DAILY_WINDOW_POLICY, map_bar_event, ms_to_utc
from app.infrastructure.polygon.schemas import PolygonAggBar, PolygonAggsResponse
from app.market_data.enums import AdjustmentState, AssetClass
from app.market_data.identity import InstrumentId
from app.market_data.keys import build_deduplication_key, build_idempotency_key
from app.market_data.serialization import market_event_to_envelope, market_event_to_payload
from pydantic import SecretStr
from tests.conftest import VALID_PROD_JWT_SECRET

API_KEY = "test-polygon-key-value"
BASE = "https://api.polygon.io"


def _instrument() -> InstrumentId:
    return InstrumentId(
        instrument_key="bergama:equity:us:aapl",
        asset_class=AssetClass.EQUITY,
        local_symbol="AAPL",
        symbol_effective_from=datetime(2020, 1, 1, tzinfo=UTC),
    )


def _settings(**overrides: Any) -> PolygonSettings:
    base: dict[str, Any] = {
        "enabled": True,
        "api_key": SecretStr(API_KEY),
        "base_url": BASE,
        "max_retries": 3,
        "retry_initial_delay_seconds": 0.01,
        "retry_max_delay_seconds": 0.05,
        "retry_after_max_seconds": 1.0,
        "max_pages": 5,
        "max_results_per_page": 5_000,
    }
    base.update(overrides)
    return PolygonSettings(**base)


def _bar(
    *,
    t_ms: int,
    o: float = 10,
    h: float = 12,
    low: float = 9,
    c: float = 11,
    v: float = 1000,
) -> dict[str, Any]:
    return {"o": o, "h": h, "l": low, "c": c, "v": v, "vw": 10.5, "t": t_ms, "n": 2}


def _ok_body(
    results: list[dict[str, Any]],
    *,
    request_id: str = "req-1",
    next_url: str | None = None,
    adjusted: bool = True,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "status": "OK",
        "request_id": request_id,
        "ticker": "AAPL",
        "adjusted": adjusted,
        "resultsCount": len(results),
        "results": results,
    }
    if next_url is not None:
        body["next_url"] = next_url
    return body


class _Sleeper:
    def __init__(self) -> None:
        self.delays: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


async def _connector(
    handler: httpx.MockTransport | Any,
    *,
    settings: PolygonSettings | None = None,
    clock: FixedClock | None = None,
    sleeper: _Sleeper | None = None,
) -> tuple[PolygonHistoricalConnector, PolygonHttpClient, _Sleeper]:
    resolved_settings = settings or _settings()
    resolved_sleeper = sleeper or _Sleeper()
    if isinstance(handler, httpx.MockTransport):
        transport = handler
    else:
        transport = httpx.MockTransport(handler)
    http = PolygonHttpClient(resolved_settings, transport=transport, sleeper=resolved_sleeper)
    clock = clock or FixedClock(datetime(2024, 6, 15, 12, 0, tzinfo=UTC))
    return PolygonHistoricalConnector(http, clock=clock), http, resolved_sleeper


def _request(
    *,
    timespan: PolygonTimespan = PolygonTimespan.DAY,
    multiplier: int = 1,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int | None = 100,
    adjusted: bool | None = None,
) -> HistoricalBarsRequest:
    start = start or datetime(2024, 1, 2, tzinfo=UTC)
    end = end or datetime(2024, 1, 3, tzinfo=UTC)
    return HistoricalBarsRequest(
        symbol="AAPL",
        instrument=_instrument(),
        currency="USD",
        venue="XNAS",
        timespan=timespan,
        multiplier=multiplier,
        start=start,
        end=end,
        limit=limit,
        adjusted=adjusted,
    )


@pytest.mark.asyncio
async def test_single_page_minute_hour_day() -> None:
    t_ms = 1_704_196_800_000  # 2024-01-02 12:00:00 UTC

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("Authorization") == f"Bearer {API_KEY}"
        assert "apiKey" not in str(request.url)
        results = [_bar(t_ms=t_ms)]
        return httpx.Response(200, json=_ok_body(results))

    for timespan, expected_delta in (
        (PolygonTimespan.MINUTE, timedelta(minutes=1)),
        (PolygonTimespan.HOUR, timedelta(hours=1)),
        (PolygonTimespan.DAY, timedelta(days=1)),
    ):
        connector, http, _ = await _connector(handler)
        try:
            result = await connector.fetch_bars(_request(timespan=timespan))
        finally:
            await http.aclose()
        assert result.pages_fetched == 1
        assert len(result.bars) == 1
        bar = result.bars[0]
        assert bar.window_end - bar.window_start == expected_delta
        assert bar.instrument.instrument_key == "bergama:equity:us:aapl"
        assert bar.currency == "USD"
        if timespan is PolygonTimespan.DAY:
            assert bar.source.extras.get("window_policy") == DAILY_WINDOW_POLICY


@pytest.mark.asyncio
async def test_empty_response() -> None:
    connector, http, _ = await _connector(lambda _r: httpx.Response(200, json=_ok_body([])))
    try:
        result = await connector.fetch_bars(_request())
    finally:
        await http.aclose()
    assert result.bars == ()
    assert result.pages_fetched == 1


@pytest.mark.asyncio
async def test_multi_page_preserves_order_no_silent_dedupe() -> None:
    page1 = "https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/1/2?cursor=page1"
    page2 = "https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/1/2?cursor=page2"
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if "cursor=page2" in str(request.url):
            return httpx.Response(
                200,
                json=_ok_body([_bar(t_ms=2, o=2, h=2, low=2, c=2)], request_id="req-2"),
            )
        if request.url.path.startswith("/v2/aggs"):
            return httpx.Response(
                200,
                json=_ok_body(
                    [_bar(t_ms=1, o=1, h=1, low=1, c=1), _bar(t_ms=1, o=1, h=1, low=1, c=1)],
                    next_url=page2,
                    request_id="req-1",
                ),
            )
        raise AssertionError(f"unexpected url {request.url}")

    connector, http, _ = await _connector(handler)
    try:
        result = await connector.fetch_bars(_request())
    finally:
        await http.aclose()
    assert result.pages_fetched == 2
    assert len(result.bars) == 3
    assert [b.open for b in result.bars] == [Decimal("1"), Decimal("1"), Decimal("2")]
    assert page1 not in "".join(calls)  # first page is relative path


@pytest.mark.asyncio
async def test_pagination_loop_detected() -> None:
    loop_url = "https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/1/2?cursor=loop"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=_ok_body([_bar(t_ms=1, o=1, h=1, low=1, c=1)], next_url=loop_url),
        )

    connector, http, _ = await _connector(handler)
    try:
        with pytest.raises(PolygonPaginationLoopError):
            await connector.fetch_bars(_request())
    finally:
        await http.aclose()


@pytest.mark.asyncio
async def test_pagination_page_limit() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        cursor = parse_qs(urlparse(str(request.url)).query).get("cursor", ["0"])[0]
        nxt = f"https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/1/2?cursor={int(cursor) + 1}"
        return httpx.Response(
            200,
            json=_ok_body([_bar(t_ms=1, o=1, h=1, low=1, c=1)], next_url=nxt),
        )

    connector, http, _ = await _connector(handler, settings=_settings(max_pages=2))
    try:
        with pytest.raises(PolygonPaginationLimitError):
            await connector.fetch_bars(_request())
    finally:
        await http.aclose()


@pytest.mark.asyncio
async def test_cross_host_and_scheme_downgrade_next_url() -> None:
    def cross_host(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=_ok_body(
                [_bar(t_ms=1, o=1, h=1, low=1, c=1)],
                next_url="https://evil.example/v2/aggs",
            ),
        )

    connector, http, _ = await _connector(cross_host)
    try:
        with pytest.raises(PolygonInvalidRequestError, match="host"):
            await connector.fetch_bars(_request())
    finally:
        await http.aclose()

    def downgrade(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=_ok_body(
                [_bar(t_ms=1, o=1, h=1, low=1, c=1)],
                next_url="http://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/1/2",
            ),
        )

    connector, http, _ = await _connector(downgrade)
    try:
        with pytest.raises(PolygonInvalidRequestError, match="scheme"):
            await connector.fetch_bars(_request())
    finally:
        await http.aclose()


@pytest.mark.asyncio
async def test_429_retry_after_then_success() -> None:
    state = {"n": 0}
    sleeper = _Sleeper()

    def handler(_request: httpx.Request) -> httpx.Response:
        state["n"] += 1
        if state["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "0.5"}, json={"status": "ERROR"})
        return httpx.Response(200, json=_ok_body([_bar(t_ms=1, o=1, h=1, low=1, c=1)]))

    connector, http, _ = await _connector(handler, sleeper=sleeper)
    try:
        result = await connector.fetch_bars(_request())
    finally:
        await http.aclose()
    assert len(result.bars) == 1
    assert sleeper.delays and sleeper.delays[0] == 0.5


@pytest.mark.asyncio
async def test_transient_5xx_then_success() -> None:
    state = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        state["n"] += 1
        if state["n"] < 3:
            return httpx.Response(503, json={"status": "ERROR"})
        return httpx.Response(200, json=_ok_body([_bar(t_ms=1, o=1, h=1, low=1, c=1)]))

    connector, http, sleeper = await _connector(handler)
    try:
        result = await connector.fetch_bars(_request())
    finally:
        await http.aclose()
    assert len(result.bars) == 1
    assert len(sleeper.delays) == 2


@pytest.mark.asyncio
async def test_retry_exhaustion_rate_limit() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "1"}, json={"status": "ERROR"})

    connector, http, _ = await _connector(handler, settings=_settings(max_retries=2))
    try:
        with pytest.raises(PolygonRateLimitedError):
            await connector.fetch_bars(_request())
    finally:
        await http.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "exc"),
    [
        (400, PolygonInvalidRequestError),
        (401, PolygonAuthenticationFailedError),
        (403, PolygonForbiddenError),
        (404, PolygonNotFoundError),
    ],
)
async def test_client_errors_no_retry(status: int, exc: type[Exception]) -> None:
    calls = {"n": 0}
    sleeper = _Sleeper()

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(status, json={"status": "ERROR"})

    connector, http, _ = await _connector(handler, sleeper=sleeper)
    try:
        with pytest.raises(exc):
            await connector.fetch_bars(_request())
    finally:
        await http.aclose()
    assert calls["n"] == 1
    assert sleeper.delays == []


@pytest.mark.asyncio
async def test_timeout_and_connection_error_translation() -> None:
    def timeout(_request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("read timeout")

    connector, http, _ = await _connector(timeout, settings=_settings(max_retries=1))
    try:
        with pytest.raises(PolygonTimeoutError):
            await connector.fetch_bars(_request())
    finally:
        await http.aclose()

    def conn(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    connector, http, _ = await _connector(conn, settings=_settings(max_retries=1))
    try:
        with pytest.raises(PolygonConnectionFailedError):
            await connector.fetch_bars(_request())
    finally:
        await http.aclose()


@pytest.mark.asyncio
async def test_malformed_provider_response() -> None:
    connector, http, _ = await _connector(
        lambda _r: httpx.Response(200, json={"status": "OK", "results": [{"bad": True}]})
    )
    try:
        with pytest.raises(PolygonInvalidResponseError):
            await connector.fetch_bars(_request())
    finally:
        await http.aclose()


@pytest.mark.asyncio
async def test_limit_validation() -> None:
    connector, http, _ = await _connector(
        lambda _r: httpx.Response(200, json=_ok_body([])),
        settings=_settings(max_results_per_page=100),
    )
    try:
        with pytest.raises(PolygonInvalidRequestError, match="limit"):
            await connector.fetch_bars(_request(limit=101))
    finally:
        await http.aclose()


@pytest.mark.asyncio
async def test_mapping_errors_nan_ohlc_negative_volume() -> None:
    clock = FixedClock(datetime(2024, 1, 2, 12, 0, tzinfo=UTC))
    response = PolygonAggsResponse(status="OK", request_id="r", ticker="AAPL", adjusted=True)

    for payload in (
        {"o": "NaN", "h": 1, "l": 1, "c": 1, "v": 1, "t": 1_700_000_000_000},
        {"o": 1, "h": 1, "l": 2, "c": 1, "v": 1, "t": 1_700_000_000_000},  # high < low
        {"o": 1, "h": 1, "l": 1, "c": 1, "v": -5, "t": 1_700_000_000_000},
    ):
        bar = PolygonAggBar.model_validate(payload)
        with pytest.raises((PolygonMappingFailedError, ValueError)):
            map_bar_event(
                bar,
                response=response,
                instrument=_instrument(),
                currency="USD",
                venue=None,
                timespan="minute",
                multiplier=1,
                requested_adjusted=True,
                known_at=clock.now(),
                clock=clock,
                endpoint_ref="https://api.polygon.io/x",
                bar_index=0,
                request_symbol="AAPL",
            )


@pytest.mark.asyncio
async def test_adjusted_unadjusted_decimal_identity_keys_envelope() -> None:
    t_ms = 1_704_196_800_000

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=_ok_body(
                [{"o": "10.125", "h": "11", "l": "9.5", "c": "10.5", "v": "100", "t": t_ms}],
                adjusted=False,
            ),
        )

    connector, http, _ = await _connector(handler)
    try:
        result = await connector.fetch_bars(_request(adjusted=False))
    finally:
        await http.aclose()
    bar = result.bars[0]
    assert bar.adjustment_state is AdjustmentState.UNADJUSTED
    assert bar.open == Decimal("10.125")
    assert bar.instrument.instrument_key == "bergama:equity:us:aapl"
    assert bar.currency == "USD"
    assert bar.source.source_symbol == "AAPL"
    assert bar.source.source_event_id.startswith("req-1:")
    assert API_KEY not in (bar.source.source_payload_ref or "")
    assert "apiKey" not in (bar.source.source_payload_ref or "").lower()
    idem = build_idempotency_key(bar)
    dedup = build_deduplication_key(bar)
    assert idem == build_idempotency_key(bar)
    assert dedup == build_deduplication_key(bar)
    dumped = bar.model_dump()
    assert "polygon_ticker" not in dumped
    assert "o" not in dumped
    payload = market_event_to_payload(bar)
    assert payload["open"] == "10.125"
    env = market_event_to_envelope(bar)
    assert env.occurred_at == bar.occurred_at
    assert env.ingested_at == bar.ingested_at
    assert json.loads(json.dumps(payload))["currency"] == "USD"


def test_utc_and_dst_session_boundary_minute_hour() -> None:
    # US DST spring-forward 2024-03-10 02:00 local; UTC duration remains exact.
    start = ms_to_utc(1_710_054_000_000)  # 2024-03-10 07:00:00 UTC
    end_hour = start + timedelta(hours=2)
    assert (end_hour - start).total_seconds() == 7200
    end_min = start + timedelta(minutes=90)
    assert (end_min - start).total_seconds() == 5400
    # Daily policy is fixed 24h from provider t — not NYSE close.
    day_start = datetime(2024, 3, 10, 5, 0, tzinfo=UTC)
    assert (day_start + timedelta(days=1)) - day_start == timedelta(days=1)


@pytest.mark.asyncio
async def test_late_arrival_pit_flag_when_known_after_ingest() -> None:
    clock = FixedClock(datetime(2024, 1, 2, 12, 0, tzinfo=UTC))
    known_at = datetime(2024, 1, 2, 12, 0, 5, tzinfo=UTC)
    response = PolygonAggsResponse(status="OK", request_id="r", ticker="AAPL", adjusted=True)
    bar = PolygonAggBar.model_validate(_bar(t_ms=1_700_000_000_000, o=1, h=1, low=1, c=1))
    event = map_bar_event(
        bar,
        response=response,
        instrument=_instrument(),
        currency="USD",
        venue=None,
        timespan="minute",
        multiplier=1,
        requested_adjusted=True,
        known_at=known_at,
        clock=clock,
        endpoint_ref="https://api.polygon.io/x",
        bar_index=0,
        request_symbol="AAPL",
    )
    assert event.quality.is_late is True
    assert event.quality.late_arrival_lag_ms == 5000


@pytest.mark.asyncio
async def test_no_secret_in_logs_or_errors(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"status": "ERROR", "error": "unauthorized"})

    connector, http, _ = await _connector(handler)
    try:
        with pytest.raises(PolygonAuthenticationFailedError) as err:
            await connector.fetch_bars(_request())
        assert API_KEY not in str(err.value)
    finally:
        await http.aclose()
    joined = " ".join(r.message for r in caplog.records) + " ".join(
        str(getattr(r, "msg", "")) for r in caplog.records
    )
    assert API_KEY not in joined
    assert API_KEY not in caplog.text


@pytest.mark.asyncio
async def test_container_disabled_creates_no_client() -> None:
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        polygon=PolygonSettings(enabled=False),
    )
    container = build_container(settings)
    assert container.polygon_http is None
    assert container.polygon_historical is None


@pytest.mark.asyncio
async def test_separate_containers_do_not_share_clients_and_shutdown() -> None:
    sleeper = _Sleeper()
    transport = httpx.MockTransport(
        lambda _r: httpx.Response(200, json=_ok_body([_bar(t_ms=1, o=1, h=1, low=1, c=1)]))
    )
    http_a = PolygonHttpClient(_settings(), transport=transport, sleeper=sleeper)
    http_b = PolygonHttpClient(_settings(), transport=transport, sleeper=sleeper)
    assert http_a is not http_b

    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        polygon=_settings(),
    )
    c1 = build_container(settings, polygon_http=http_a)
    c2 = build_container(settings, polygon_http=http_b)
    assert c1.polygon_http is http_a
    assert c2.polygon_http is http_b
    assert c1.polygon_historical is not c2.polygon_historical
    await c1.aclose()
    await c2.aclose()


@pytest.mark.asyncio
async def test_provider_error_after_retryable_exhaustion() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"status": "ERROR"})

    connector, http, _ = await _connector(handler, settings=_settings(max_retries=2))
    try:
        with pytest.raises(PolygonProviderError):
            await connector.fetch_bars(_request())
    finally:
        await http.aclose()
