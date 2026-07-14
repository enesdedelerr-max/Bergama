"""Offline Benzinga news connector tests (Issue #304D)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from app.core.benzinga_settings import BenzingaSettings
from app.core.clock import FixedClock
from app.core.config import AppSettings
from app.core.container import build_container
from app.core.environment import AppEnvironment
from app.core.secrets import SecretSettings
from app.infrastructure.benzinga.errors import (
    BenzingaAuthenticationFailedError,
    BenzingaConnectionFailedError,
    BenzingaEntitlementRequiredError,
    BenzingaInvalidResponseError,
    BenzingaMappingFailedError,
    BenzingaPaginationLimitError,
    BenzingaPaginationLoopError,
    BenzingaProviderError,
    BenzingaRateLimitedError,
    BenzingaTimeoutError,
)
from app.infrastructure.benzinga.http import BenzingaHttpClient
from app.infrastructure.benzinga.mapper import (
    format_updated_iso,
    map_news_item,
    normalize_ticker_for_lookup,
    parse_benzinga_timestamp,
    validate_article_url,
)
from app.infrastructure.benzinga.news import BenzingaNewsConnector, NewsRequest
from app.infrastructure.benzinga.pagination import PagePaginationGuard, sanitize_url
from app.infrastructure.benzinga.schemas import BenzingaNewsItem
from app.market_data.enums import AssetClass
from app.market_data.identity import InstrumentId
from app.market_data.keys import build_deduplication_key, build_idempotency_key
from app.market_data.serialization import market_event_to_envelope, market_event_to_payload
from pydantic import SecretStr, ValidationError
from tests.conftest import VALID_PROD_JWT_SECRET

API_KEY = "test-benzinga-key-value-abcdefghijklmnop"
BASE = "https://api.benzinga.com"
OBSERVED = datetime(2024, 6, 15, 16, 0, tzinfo=UTC)
CREATED = "Mon, 01 Jan 2024 13:35:14 -0400"
UPDATED = "Mon, 01 Jan 2024 13:35:15 -0400"
UPDATED_LATER = "Mon, 01 Jan 2024 14:00:00 -0400"


def _instrument(key: str = "bergama:equity:us:aapl", symbol: str = "AAPL") -> InstrumentId:
    return InstrumentId(
        instrument_key=key,
        asset_class=AssetClass.EQUITY,
        local_symbol=symbol,
        symbol_effective_from=datetime(2020, 1, 1, tzinfo=UTC),
    )


def _anchor() -> InstrumentId:
    return InstrumentId(
        instrument_key="bergama:news:anchor:test",
        asset_class=AssetClass.OTHER,
        local_symbol=None,
        symbol_effective_from=datetime(2020, 1, 1, tzinfo=UTC),
    )


def _settings(**overrides: object) -> BenzingaSettings:
    base: dict[str, object] = {
        "enabled": True,
        "api_key": SecretStr(API_KEY),
        "base_url": BASE,
        "max_retries": 3,
        "retry_initial_delay_seconds": 0.01,
        "retry_max_delay_seconds": 0.05,
        "max_retry_after_seconds": 1.0,
        "page_size": 2,
        "max_pages": 3,
        "default_display_output": "abstract",
    }
    base.update(overrides)
    return BenzingaSettings(**base)


def _story(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": 36444586,
        "author": "Synthetic Desk",
        "created": CREATED,
        "updated": UPDATED,
        "title": "Synthetic fixtures only — no copyrighted content",
        "teaser": "Synthetic teaser for unit tests.",
        "body": "SYNTHETIC_FULL_BODY_MUST_NEVER_BE_MAPPED",
        "url": "https://www.benzinga.com/news/test/36444586/synthetic-fixture",
        "channels": [{"name": "Markets"}, {"name": "Equities"}],
        "tags": [{"name": "Synthetic"}],
        "stocks": [{"name": "AAPL", "exchange": "NASDAQ"}],
        "importance_rank": 2,
        "original_id": 1001,
    }
    data.update(overrides)
    return data


class _Sleeper:
    def __init__(self) -> None:
        self.delays: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


def test_settings_disabled_by_default() -> None:
    settings = BenzingaSettings()
    assert settings.enabled is False
    assert settings.api_key is None
    assert settings.default_display_output == "abstract"


def test_api_key_required_when_enabled_and_redacted() -> None:
    with pytest.raises(ValidationError, match="API_KEY"):
        BenzingaSettings(enabled=True)
    configured = _settings()
    summary = configured.safe_summary()
    assert summary["api_key_configured"] is True
    assert API_KEY not in str(summary)
    assert API_KEY not in repr(configured)


def test_full_display_rejected_in_settings_and_request() -> None:
    with pytest.raises(ValidationError, match="full"):
        BenzingaSettings(enabled=True, api_key=SecretStr(API_KEY), default_display_output="full")  # type: ignore[arg-type]
    with pytest.raises(ValidationError, match="full"):
        NewsRequest(date="2024-01-01", display_output="full")  # type: ignore[arg-type]


def test_request_requires_bound_and_rejects_partial_range() -> None:
    with pytest.raises(ValidationError, match="bounded"):
        NewsRequest(page_size=1)
    with pytest.raises(ValidationError, match="together"):
        NewsRequest(date_from="2024-01-01")
    ok = NewsRequest(date="2024-01-01", page_size=5, anchor_instrument=_anchor())
    assert ok.date == "2024-01-01"


def test_sanitize_url_redacts_token() -> None:
    url = f"{BASE}/api/v2/news?page=0&token={API_KEY}"
    cleaned = sanitize_url(url)
    assert API_KEY not in cleaned
    assert "token" not in cleaned.lower()
    assert "page=0" in cleaned


def test_ticker_normalization_is_narrow() -> None:
    assert normalize_ticker_for_lookup(" aapl ") == "AAPL"
    assert normalize_ticker_for_lookup("BRK.B") == "BRK.B"


def test_url_host_and_scheme_validation() -> None:
    assert validate_article_url("https://www.benzinga.com/news/1") is not None
    with pytest.raises(BenzingaMappingFailedError, match="scheme"):
        validate_article_url("ftp://www.benzinga.com/x")
    with pytest.raises(BenzingaMappingFailedError, match="host"):
        validate_article_url("https://evil.example/x")
    with pytest.raises(BenzingaMappingFailedError, match="credentials"):
        validate_article_url("https://user:pass@www.benzinga.com/x")


def test_timestamp_parsing_rejects_naive() -> None:
    aware = parse_benzinga_timestamp(CREATED, field_name="created")
    assert aware.tzinfo is not None
    with pytest.raises(BenzingaMappingFailedError):
        parse_benzinga_timestamp("not-a-date", field_name="created")


def test_revision_identity_distinct_keys() -> None:
    item1 = BenzingaNewsItem.model_validate(_story())
    item2 = BenzingaNewsItem.model_validate(_story(updated=UPDATED_LATER))
    events1 = map_news_item(
        item1,
        ticker_to_instrument={"AAPL": _instrument()},
        anchor_instrument=None,
        observed_at=OBSERVED,
        endpoint_ref=f"{BASE}/api/v2/news?page=0",
    )
    events2 = map_news_item(
        item2,
        ticker_to_instrument={"AAPL": _instrument()},
        anchor_instrument=None,
        observed_at=OBSERVED,
        endpoint_ref=f"{BASE}/api/v2/news?page=0",
    )
    e1, e2 = events1[0], events2[0]
    assert e1.source.source_event_id != e2.source.source_event_id
    assert build_idempotency_key(e1) != build_idempotency_key(e2)
    assert build_deduplication_key(e1) != build_deduplication_key(e2)
    assert e1.quality.is_revision is False
    assert e1.quality.revision_of_event_id is None
    assert "original_id" in e1.metadata
    assert e1.metadata["original_id"] == "1001"
    assert "SYNTHETIC_FULL_BODY" not in str(e1.model_dump())
    assert e1.summary == "Synthetic teaser for unit tests."
    assert "sentiment" not in e1.metadata
    assert "catalyst" not in e1.metadata
    updated = parse_benzinga_timestamp(UPDATED, field_name="updated")
    assert e1.source.source_event_id == f"36444586:{format_updated_iso(updated)}"


def test_zero_ticker_requires_anchor_and_maps() -> None:
    item = BenzingaNewsItem.model_validate(_story(stocks=[]))
    with pytest.raises(BenzingaMappingFailedError, match="anchor_instrument"):
        map_news_item(
            item,
            ticker_to_instrument={},
            anchor_instrument=None,
            observed_at=OBSERVED,
            endpoint_ref="https://api.benzinga.com/api/v2/news",
        )
    events = map_news_item(
        item,
        ticker_to_instrument={},
        anchor_instrument=_anchor(),
        observed_at=OBSERVED,
        endpoint_ref="https://api.benzinga.com/api/v2/news",
    )
    assert len(events) == 1
    assert events[0].instrument.instrument_key == "bergama:news:anchor:test"


def test_unmapped_tickers_fail_without_anchor_and_preserve_with_anchor() -> None:
    item = BenzingaNewsItem.model_validate(_story(stocks=[{"name": "ZZZZ"}]))
    with pytest.raises(BenzingaMappingFailedError, match="none mapped"):
        map_news_item(
            item,
            ticker_to_instrument={},
            anchor_instrument=None,
            observed_at=OBSERVED,
            endpoint_ref="https://api.benzinga.com/api/v2/news",
        )
    events = map_news_item(
        item,
        ticker_to_instrument={},
        anchor_instrument=_anchor(),
        observed_at=OBSERVED,
        endpoint_ref="https://api.benzinga.com/api/v2/news",
    )
    assert events[0].metadata["provider_tickers"] == "ZZZZ"


def test_multi_ticker_fan_out_and_duplicate_order() -> None:
    item = BenzingaNewsItem.model_validate(
        _story(
            stocks=[
                {"name": "AAPL"},
                {"name": "AAPL"},
                {"name": "msft"},
                {"name": "NVDA"},
            ]
        )
    )
    mapping = {
        "AAPL": _instrument("bergama:equity:us:aapl", "AAPL"),
        "MSFT": _instrument("bergama:equity:us:msft", "MSFT"),
    }
    events = map_news_item(
        item,
        ticker_to_instrument=mapping,
        anchor_instrument=None,
        observed_at=OBSERVED,
        endpoint_ref="https://api.benzinga.com/api/v2/news",
    )
    assert len(events) == 2
    assert [e.instrument.local_symbol for e in events] == ["AAPL", "MSFT"]
    assert events[0].metadata["provider_tickers"] == "AAPL,msft,NVDA"
    assert "NVDA" in events[0].metadata["provider_tickers"]
    keys = {e.source.source_event_id for e in events}
    assert len(keys) == 1


def test_summary_truncation_and_topics() -> None:
    long_teaser = "x" * 5000
    item = BenzingaNewsItem.model_validate(_story(teaser=long_teaser))
    events = map_news_item(
        item,
        ticker_to_instrument={"AAPL": _instrument()},
        anchor_instrument=None,
        observed_at=OBSERVED,
        endpoint_ref="https://api.benzinga.com/api/v2/news",
    )
    assert events[0].summary is not None
    assert len(events[0].summary) == 4096
    assert events[0].topics[:3] == ("Markets", "Equities", "Synthetic")
    assert events[0].metadata["author"] == "Synthetic Desk"
    assert events[0].metadata["importance_rank"] == "2"


def test_pagination_guard_detects_loop_and_limit() -> None:
    guard = PagePaginationGuard(max_pages=2)
    guard.begin_page(0)
    with pytest.raises(BenzingaPaginationLoopError):
        guard.begin_page(0)
    guard2 = PagePaginationGuard(max_pages=1)
    guard2.begin_page(0)
    with pytest.raises(BenzingaPaginationLimitError):
        guard2.begin_page(1)


@pytest.mark.asyncio
async def test_auth_header_no_query_token_and_single_page() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        assert request.headers.get("Authorization") == f"token {API_KEY}"
        assert "token" not in request.url.params
        assert request.url.params.get("displayOutput") == "abstract"
        assert request.url.params.get("date") == "2024-01-01"
        return httpx.Response(200, json=[_story()])

    http = BenzingaHttpClient(
        _settings(),
        transport=httpx.MockTransport(handler),
        sleeper=_Sleeper(),
    )
    connector = BenzingaNewsConnector(http, clock=FixedClock(OBSERVED))
    result = await connector.fetch_news(
        NewsRequest(
            date="2024-01-01",
            page_size=2,
            ticker_to_instrument={"AAPL": _instrument()},
        )
    )
    await http.aclose()
    assert result.stories_seen == 1
    assert result.pages_fetched == 1
    assert result.may_have_more is False
    assert len(result.events) == 1
    assert result.events[0].known_at == OBSERVED
    assert result.events[0].ingested_at == OBSERVED
    assert API_KEY not in result.endpoint_refs[0]
    env = market_event_to_envelope(result.events[0])
    payload = market_event_to_payload(result.events[0])
    assert env.idempotency_key == build_idempotency_key(result.events[0])
    assert payload["headline"] == result.events[0].headline
    assert "body" not in payload
    assert len(seen) == 1


@pytest.mark.asyncio
async def test_headline_mode_and_empty_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params.get("displayOutput") == "headline"
        return httpx.Response(200, json=[])

    http = BenzingaHttpClient(
        _settings(default_display_output="headline"),
        transport=httpx.MockTransport(handler),
        sleeper=_Sleeper(),
    )
    connector = BenzingaNewsConnector(http, clock=FixedClock(OBSERVED))
    result = await connector.fetch_news(
        NewsRequest(updated_since=1, page_size=5, anchor_instrument=_anchor())
    )
    await http.aclose()
    assert result.events == ()
    assert result.stories_seen == 0


@pytest.mark.asyncio
async def test_multi_page_and_may_have_more() -> None:
    pages: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        pages.append(page)
        items = [_story(id=page * 10 + i, stocks=[{"name": "AAPL"}]) for i in range(2)]
        return httpx.Response(200, json=items)

    http = BenzingaHttpClient(
        _settings(max_pages=2, page_size=2),
        transport=httpx.MockTransport(handler),
        sleeper=_Sleeper(),
    )
    connector = BenzingaNewsConnector(http, clock=FixedClock(OBSERVED))
    result = await connector.fetch_news(
        NewsRequest(
            date="2024-01-01",
            page_size=2,
            ticker_to_instrument={"AAPL": _instrument()},
        )
    )
    await http.aclose()
    assert pages == [0, 1]
    assert result.pages_fetched == 2
    assert result.may_have_more is True
    assert result.stories_seen == 4
    assert len(result.events) == 4


@pytest.mark.asyncio
async def test_malformed_response() -> None:
    http = BenzingaHttpClient(
        _settings(),
        transport=httpx.MockTransport(lambda _r: httpx.Response(200, json={"ok": True})),
        sleeper=_Sleeper(),
    )
    connector = BenzingaNewsConnector(http, clock=FixedClock(OBSERVED))
    with pytest.raises(BenzingaInvalidResponseError, match="array"):
        await connector.fetch_news(NewsRequest(date="2024-01-01", anchor_instrument=_anchor()))
    await http.aclose()


@pytest.mark.asyncio
async def test_401_403_no_retry_and_429_retry_after() -> None:
    sleeper = _Sleeper()

    def auth_fail(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"ok": False})

    http = BenzingaHttpClient(
        _settings(),
        transport=httpx.MockTransport(auth_fail),
        sleeper=sleeper,
    )
    connector = BenzingaNewsConnector(http, clock=FixedClock(OBSERVED))
    with pytest.raises(BenzingaAuthenticationFailedError):
        await connector.fetch_news(NewsRequest(date="2024-01-01", anchor_instrument=_anchor()))
    await http.aclose()
    assert sleeper.delays == []

    def entitlement(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"ok": False})

    sleeper2 = _Sleeper()
    http2 = BenzingaHttpClient(
        _settings(), transport=httpx.MockTransport(entitlement), sleeper=sleeper2
    )
    connector2 = BenzingaNewsConnector(http2, clock=FixedClock(OBSERVED))
    with pytest.raises(BenzingaEntitlementRequiredError):
        await connector2.fetch_news(NewsRequest(date="2024-01-01", anchor_instrument=_anchor()))
    await http2.aclose()
    assert sleeper2.delays == []

    calls = {"n": 0}

    def rate_limited(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(429, headers={"Retry-After": "0.01"}, json={})
        return httpx.Response(200, json=[])

    sleeper3 = _Sleeper()
    http3 = BenzingaHttpClient(
        _settings(), transport=httpx.MockTransport(rate_limited), sleeper=sleeper3
    )
    connector3 = BenzingaNewsConnector(http3, clock=FixedClock(OBSERVED))
    result = await connector3.fetch_news(
        NewsRequest(date="2024-01-01", anchor_instrument=_anchor())
    )
    await http3.aclose()
    assert result.stories_seen == 0
    assert sleeper3.delays


@pytest.mark.asyncio
async def test_5xx_retry_then_rate_limit_exhausted_and_transport_errors() -> None:
    sleeper = _Sleeper()
    count = {"n": 0}

    def always_500(_request: httpx.Request) -> httpx.Response:
        count["n"] += 1
        return httpx.Response(500, json={})

    http = BenzingaHttpClient(
        _settings(max_retries=2),
        transport=httpx.MockTransport(always_500),
        sleeper=sleeper,
    )
    with pytest.raises(BenzingaProviderError):
        await http.get("/api/v2/news", params={"page": 0})
    await http.aclose()
    assert count["n"] == 2
    assert sleeper.delays

    sleeper2 = _Sleeper()
    http2 = BenzingaHttpClient(
        _settings(max_retries=1),
        transport=httpx.MockTransport(lambda _r: httpx.Response(429, json={})),
        sleeper=sleeper2,
    )
    with pytest.raises(BenzingaRateLimitedError):
        await http2.get("/api/v2/news", params={"page": 0})
    await http2.aclose()

    def timeout(_request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout")

    http3 = BenzingaHttpClient(
        _settings(max_retries=1), transport=httpx.MockTransport(timeout), sleeper=_Sleeper()
    )
    with pytest.raises(BenzingaTimeoutError):
        await http3.get("/api/v2/news", params={"page": 0})
    await http3.aclose()

    def conn(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    http4 = BenzingaHttpClient(
        _settings(max_retries=1), transport=httpx.MockTransport(conn), sleeper=_Sleeper()
    )
    with pytest.raises(BenzingaConnectionFailedError):
        await http4.get("/api/v2/news", params={"page": 0})
    await http4.aclose()


@pytest.mark.asyncio
async def test_container_lifecycle_and_no_shared_clients(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    settings = AppSettings(
        environment=AppEnvironment.TEST,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
        benzinga=_settings(),
    )
    disabled = AppSettings(
        environment=AppEnvironment.TEST,
        secrets=SecretSettings(bootstrap_jwt_signing_key=VALID_PROD_JWT_SECRET),
    )
    c0 = build_container(disabled)
    assert c0.benzinga_http is None
    assert c0.benzinga_news is None

    c1 = build_container(settings)
    c2 = build_container(settings)
    assert c1.benzinga_http is not None
    assert c2.benzinga_http is not None
    assert c1.benzinga_http is not c2.benzinga_http
    assert c1.benzinga_news is not None
    await c1.aclose()
    await c2.aclose()
    # Closing twice is idempotent
    await c1.aclose()
