"""Offline SEC EDGAR filings connector tests (Issue #304C)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from app.core.clock import FixedClock
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.core.sec_settings import SecSettings
from app.core.secrets import SecretSettings
from app.infrastructure.sec.accession import (
    accession_without_dashes,
    normalize_cik,
    validate_accession_number,
)
from app.infrastructure.sec.errors import (
    SecConnectionFailedError,
    SecForbiddenError,
    SecInvalidCikError,
    SecInvalidRequestError,
    SecInvalidResponseError,
    SecNotFoundError,
    SecProviderError,
    SecTimeoutError,
)
from app.infrastructure.sec.http import SecHttpClient
from app.infrastructure.sec.rate_limit import MinIntervalRateLimiter
from app.infrastructure.sec.submissions import SecSubmissionsConnector, SubmissionsRequest
from app.infrastructure.sec.urls import build_filing_index_url
from app.market_data.enums import AssetClass
from app.market_data.identity import InstrumentId
from app.market_data.keys import build_deduplication_key, build_idempotency_key
from app.market_data.serialization import market_event_to_envelope, market_event_to_payload
from pydantic import ValidationError
from tests.conftest import VALID_PROD_JWT_SECRET

CONTACT = "bergama-connectors@bergama.invalid"
OBSERVED = datetime(2024, 6, 15, 12, 0, tzinfo=UTC)
CIK = "0000320193"


def _instrument() -> InstrumentId:
    return InstrumentId(
        instrument_key="bergama:equity:us:aapl",
        asset_class=AssetClass.EQUITY,
        local_symbol="AAPL",
        symbol_effective_from=datetime(2020, 1, 1, tzinfo=UTC),
    )


def _settings(**overrides: object) -> SecSettings:
    base: dict[str, object] = {
        "enabled": True,
        "contact_email": CONTACT,
        "application_name": "BergamaTrading",
        "max_retries": 3,
        "retry_initial_delay_seconds": 0.01,
        "retry_max_delay_seconds": 0.05,
        "retry_after_max_seconds": 1.0,
        "min_request_interval_seconds": 0.1,
        "max_filings_per_request": 50,
    }
    base.update(overrides)
    return SecSettings(**base)


class _Sleeper:
    def __init__(self) -> None:
        self.delays: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


def _recent_payload() -> dict[str, Any]:
    return {
        "cik": "320193",
        "entityType": "operating",
        "sic": "3571",
        "sicDescription": "Electronic Computers",
        "name": "Apple Inc.",
        "tickers": ["AAPL"],
        "exchanges": ["Nasdaq"],
        "fiscalYearEnd": "0930",
        "filings": {
            "recent": {
                "accessionNumber": [
                    "0000320193-23-000106",
                    "0000320193-23-000107",
                    "0000320193-23-000077",
                ],
                "filingDate": ["2023-11-03", "2023-11-03", "2023-08-04"],
                "reportDate": ["2023-09-30", "2023-09-30", "2023-07-01"],
                "acceptanceDateTime": [
                    "2023-11-03T06:01:27.000Z",
                    "2023-11-03T08:00:00.000Z",
                    "2023-08-04T18:04:02.000Z",
                ],
                "act": ["34", "34", "34"],
                "form": ["10-K", "10-K/A", "10-Q"],
                "fileNumber": ["001-36743", "001-36743", "001-36743"],
                "filmNumber": ["231366666", "231366667", "231111111"],
                "items": ["", "", ""],
                "size": [100, 110, 90],
                "isXBRL": [1, 1, 1],
                "isInlineXBRL": [1, 1, 0],
                "primaryDocument": ["aapl-20230930.htm", "aapl-a.htm", "aapl-20230701.htm"],
                "primaryDocDescription": ["10-K", "10-K/A", "10-Q"],
            },
            "files": [
                {
                    "name": "CIK0000320193-submissions-001.json",
                    "filingCount": 1000,
                    "filingFrom": "1994-01-01",
                    "filingTo": "2018-01-01",
                }
            ],
        },
    }


def test_settings_disabled_by_default() -> None:
    settings = SecSettings()
    assert settings.enabled is False


def test_user_agent_required_and_placeholder_rejected() -> None:
    with pytest.raises(ValidationError):
        SecSettings(enabled=True)
    with pytest.raises(ValidationError, match="placeholder|example.com|User-Agent"):
        SecSettings(enabled=True, contact_email="admin@example.com")
    with pytest.raises(ValidationError, match="generic|User-Agent"):
        SecSettings(enabled=True, user_agent="Mozilla/5.0 BergamaTrading")
    configured = _settings()
    assert CONTACT in configured.resolved_user_agent()
    summary = configured.safe_summary()
    assert summary["contact_email_configured"] is True
    assert CONTACT not in str(summary)


def test_cik_and_accession_normalization() -> None:
    assert normalize_cik("320193") == CIK
    assert normalize_cik("CIK320193") == CIK
    with pytest.raises(SecInvalidCikError):
        normalize_cik("AAPL")
    with pytest.raises(SecInvalidCikError):
        normalize_cik("0")
    accession = validate_accession_number("0000320193-23-000106")
    assert accession_without_dashes(accession) == "000032019323000106"
    with pytest.raises(SecInvalidRequestError):
        validate_accession_number("bad")


def test_filing_url_construction() -> None:
    url = build_filing_index_url(
        archives_base_url="https://www.sec.gov",
        cik=CIK,
        accession_number="0000320193-23-000106",
    )
    assert url == (
        "https://www.sec.gov/Archives/edgar/data/320193/"
        "000032019323000106/0000320193-23-000106-index.html"
    )
    with pytest.raises(SecInvalidRequestError):
        build_filing_index_url(
            archives_base_url="https://evil.example",
            cik=CIK,
            accession_number="0000320193-23-000106",
        )


@pytest.mark.asyncio
async def test_submissions_happy_path(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    seen_ua: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_ua.append(request.headers.get("User-Agent", ""))
        assert request.url.path.endswith(f"/submissions/CIK{CIK}.json")
        return httpx.Response(200, json=_recent_payload())

    sleeper = _Sleeper()
    limiter = MinIntervalRateLimiter(min_interval_seconds=0.1, sleeper=sleeper)
    http = SecHttpClient(
        _settings(),
        transport=httpx.MockTransport(handler),
        sleeper=sleeper,
        rate_limiter=limiter,
    )
    try:
        result = await SecSubmissionsConnector(http, clock=FixedClock(OBSERVED)).fetch_submissions(
            SubmissionsRequest(cik="320193", instrument=_instrument(), max_filings=10)
        )
    finally:
        await http.aclose()

    assert CONTACT in seen_ua[0]
    assert result.cik == CIK
    assert result.entity_name == "Apple Inc."
    assert result.filings_mapped == 3
    assert len(result.archive_files) == 1
    assert result.archive_files[0]["name"].startswith("CIK")

    events = result.events
    assert events[0].form_type == "10-K"
    assert events[1].form_type == "10-K/A"
    assert events[1].metadata["is_amendment"] == "true"
    assert events[1].metadata["base_form"] == "10-K"
    assert events[0].instrument.instrument_key == "bergama:equity:us:aapl"
    assert events[0].source.provider == "sec_edgar"
    assert events[0].source.source_instrument_id == CIK
    assert events[0].source.source_event_id == ("0000320193:0000320193-23-000106:10-K:2023-11-03")
    assert events[0].accession_number == "0000320193-23-000106"
    assert events[0].document_ref.endswith("-index.html")
    assert events[0].metadata["sec_is_xbrl"] == "true"
    assert events[0].effective_at == datetime(2023, 11, 3, tzinfo=UTC)
    assert events[0].known_at == datetime(2023, 11, 3, 6, 1, 27, tzinfo=UTC)
    assert events[0].occurred_at == events[0].known_at
    assert events[0].ingested_at == OBSERVED

    # Original vs amendment remain distinct via accession/form/time in keys.
    assert build_deduplication_key(events[0]) != build_deduplication_key(events[1])
    assert build_idempotency_key(events[0]) != build_idempotency_key(events[1])
    assert "0000320193" in events[0].source.source_event_id
    assert "10-K/A" in events[1].source.source_event_id

    payload = market_event_to_payload(events[0])
    env = market_event_to_envelope(events[0])
    assert payload["accession_number"] == events[0].accession_number
    assert env.payload["form_type"] == "10-K"
    assert "raw" not in caplog.text.lower() or "payload" not in caplog.text.lower()


@pytest.mark.asyncio
async def test_malformed_array_lengths_rejected() -> None:
    bad = _recent_payload()
    bad["filings"]["recent"]["form"] = ["10-K"]

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=bad)

    http = SecHttpClient(
        _settings(),
        transport=httpx.MockTransport(handler),
        sleeper=_Sleeper(),
        rate_limiter=MinIntervalRateLimiter(min_interval_seconds=0.1, sleeper=_Sleeper()),
    )
    try:
        with pytest.raises(SecInvalidResponseError):
            await SecSubmissionsConnector(http, clock=FixedClock(OBSERVED)).fetch_submissions(
                SubmissionsRequest(cik=CIK, instrument=_instrument())
            )
    finally:
        await http.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "exc"),
    [
        (400, SecInvalidRequestError),
        (403, SecForbiddenError),
        (404, SecNotFoundError),
    ],
)
async def test_client_errors_no_retry(status: int, exc: type[Exception]) -> None:
    calls = {"n": 0}
    sleeper = _Sleeper()

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(status, json={"error": "x"})

    http = SecHttpClient(
        _settings(),
        transport=httpx.MockTransport(handler),
        sleeper=sleeper,
        rate_limiter=MinIntervalRateLimiter(min_interval_seconds=0.1, sleeper=sleeper),
    )
    try:
        with pytest.raises(exc):
            await SecSubmissionsConnector(http, clock=FixedClock(OBSERVED)).fetch_submissions(
                SubmissionsRequest(cik=CIK, instrument=_instrument())
            )
    finally:
        await http.aclose()
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_429_and_5xx_retry_and_rate_limiter() -> None:
    state = {"n": 0}
    sleeper = _Sleeper()

    def handler(_request: httpx.Request) -> httpx.Response:
        state["n"] += 1
        if state["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "0.5"}, json={})
        if state["n"] == 2:
            return httpx.Response(503, json={})
        return httpx.Response(200, json=_recent_payload())

    times = {"t": 0.0}

    def mono() -> float:
        return times["t"]

    async def advancing_sleeper(seconds: float) -> None:
        sleeper.delays.append(seconds)
        times["t"] += seconds

    limiter = MinIntervalRateLimiter(
        min_interval_seconds=0.2,
        sleeper=advancing_sleeper,
        monotonic_fn=mono,
    )
    http = SecHttpClient(
        _settings(),
        transport=httpx.MockTransport(handler),
        sleeper=advancing_sleeper,
        rate_limiter=limiter,
    )
    try:
        # First call
        await SecSubmissionsConnector(http, clock=FixedClock(OBSERVED)).fetch_submissions(
            SubmissionsRequest(cik=CIK, instrument=_instrument(), max_filings=1)
        )
        # Second call should wait for rate limiter spacing from post-retry last request.
        await SecSubmissionsConnector(http, clock=FixedClock(OBSERVED)).fetch_submissions(
            SubmissionsRequest(cik=CIK, instrument=_instrument(), max_filings=1)
        )
    finally:
        await http.aclose()

    assert 0.5 in sleeper.delays
    assert any(d >= 0.19 for d in sleeper.delays)


@pytest.mark.asyncio
async def test_retry_exhaustion_timeout_connection() -> None:
    http = SecHttpClient(
        _settings(max_retries=2),
        transport=httpx.MockTransport(lambda _r: httpx.Response(500, json={})),
        sleeper=_Sleeper(),
        rate_limiter=MinIntervalRateLimiter(min_interval_seconds=0.1, sleeper=_Sleeper()),
    )
    try:
        with pytest.raises(SecProviderError):
            await SecSubmissionsConnector(http, clock=FixedClock(OBSERVED)).fetch_submissions(
                SubmissionsRequest(cik=CIK, instrument=_instrument())
            )
    finally:
        await http.aclose()

    def timeout(_r: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout")

    http = SecHttpClient(
        _settings(max_retries=1),
        transport=httpx.MockTransport(timeout),
        sleeper=_Sleeper(),
        rate_limiter=MinIntervalRateLimiter(min_interval_seconds=0.1, sleeper=_Sleeper()),
    )
    try:
        with pytest.raises(SecTimeoutError):
            await SecSubmissionsConnector(http, clock=FixedClock(OBSERVED)).fetch_submissions(
                SubmissionsRequest(cik=CIK, instrument=_instrument())
            )
    finally:
        await http.aclose()

    def conn(_r: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    http = SecHttpClient(
        _settings(max_retries=1),
        transport=httpx.MockTransport(conn),
        sleeper=_Sleeper(),
        rate_limiter=MinIntervalRateLimiter(min_interval_seconds=0.1, sleeper=_Sleeper()),
    )
    try:
        with pytest.raises(SecConnectionFailedError):
            await SecSubmissionsConnector(http, clock=FixedClock(OBSERVED)).fetch_submissions(
                SubmissionsRequest(cik=CIK, instrument=_instrument())
            )
    finally:
        await http.aclose()


@pytest.mark.asyncio
async def test_container_disabled_and_isolation() -> None:
    disabled = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        sec=SecSettings(enabled=False),
    )
    c0 = build_container(disabled)
    assert c0.sec_http is None
    assert c0.sec_submissions is None

    settings = AppSettings(
        environment=AppEnvironment.TEST,
        bootstrap_auth_enabled=True,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        sec=_settings(),
    )
    t = httpx.MockTransport(lambda _r: httpx.Response(200, json=_recent_payload()))
    h1 = SecHttpClient(
        settings.sec,
        transport=t,
        sleeper=_Sleeper(),
        rate_limiter=MinIntervalRateLimiter(min_interval_seconds=0.1, sleeper=_Sleeper()),
    )
    h2 = SecHttpClient(
        settings.sec,
        transport=t,
        sleeper=_Sleeper(),
        rate_limiter=MinIntervalRateLimiter(min_interval_seconds=0.1, sleeper=_Sleeper()),
    )
    c1 = build_container(settings, sec_http=h1)
    c2 = build_container(settings, sec_http=h2)
    assert c1.sec_http is h1
    assert c2.sec_http is h2
    assert c1.sec_http is not c2.sec_http
    await c1.aclose()
    await c2.aclose()
