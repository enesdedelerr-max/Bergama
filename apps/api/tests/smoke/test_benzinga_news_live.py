"""Optional live Benzinga news smoke — SKIPPED unless explicitly enabled."""

from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta

import pytest
from app.core.benzinga_settings import BenzingaSettings
from app.core.clock import SystemClock
from app.infrastructure.benzinga.errors import (
    BenzingaAuthenticationFailedError,
    BenzingaEntitlementRequiredError,
)
from app.infrastructure.benzinga.http import BenzingaHttpClient
from app.infrastructure.benzinga.news import BenzingaNewsConnector, NewsRequest
from app.market_data.enums import AssetClass
from app.market_data.identity import InstrumentId
from app.market_data.serialization import market_event_to_envelope, market_event_to_payload
from pydantic import SecretStr


def _live_enabled() -> bool:
    return os.environ.get("BERGAMA_BENZINGA_SMOKE") == "1"


@pytest.mark.asyncio
async def test_benzinga_news_live_smoke() -> None:
    """
    Live policy:
    - SKIPPED when BERGAMA_BENZINGA_SMOKE is not exactly \"1\".
    - PASS only when a real Newsfeed call succeeds.
    - FAIL when explicitly enabled and the provider call fails.
    - Distinguishes authentication vs entitlement failures.
    - Never prints the API key or full story bodies.
    """
    if not _live_enabled():
        pytest.skip(
            "smoke-api-benzinga SKIPPED "
            "(set BERGAMA_BENZINGA_SMOKE=1 and BERGAMA_BENZINGA__API_KEY)"
        )

    api_key = os.environ.get("BERGAMA_BENZINGA__API_KEY", "").strip()
    if not api_key:
        pytest.fail("BERGAMA_BENZINGA_SMOKE=1 requires BERGAMA_BENZINGA__API_KEY")

    settings = BenzingaSettings(
        enabled=True,
        api_key=SecretStr(api_key),
        max_retries=2,
        page_size=1,
        max_pages=1,
        default_display_output="abstract",
    )
    http = BenzingaHttpClient(settings)
    connector = BenzingaNewsConnector(http, clock=SystemClock())
    day = date.today().isoformat()
    anchor = InstrumentId(
        instrument_key="bergama:news:anchor:smoke",
        asset_class=AssetClass.OTHER,
        local_symbol=None,
        symbol_effective_from=datetime(2020, 1, 1, tzinfo=UTC),
    )
    try:
        result = await connector.fetch_news(
            NewsRequest(
                date=day,
                page_size=1,
                display_output="abstract",
                anchor_instrument=anchor,
            )
        )
    except BenzingaAuthenticationFailedError:
        pytest.fail("benzinga authentication failed (invalid API key)")
    except BenzingaEntitlementRequiredError:
        pytest.fail("benzinga entitlement required (plan does not include Newsfeed)")
    finally:
        await http.aclose()

    # Empty day is still a successful provider call.
    assert result.pages_fetched == 1
    assert result.may_have_more is False or result.stories_seen >= 1
    if result.events:
        first = result.events[0]
        assert first.source.provider == "benzinga"
        assert first.headline
        payload = market_event_to_payload(first)
        envelope = market_event_to_envelope(first)
        assert payload["headline"] == first.headline
        assert envelope.schema_version == first.schema_version
        assert "body" not in payload
    else:
        # Empty today is a successful provider call; optionally check previous day.
        prev = (date.today() - timedelta(days=1)).isoformat()
        http2 = BenzingaHttpClient(settings)
        connector2 = BenzingaNewsConnector(http2, clock=SystemClock())
        try:
            result2 = await connector2.fetch_news(
                NewsRequest(
                    date=prev,
                    page_size=1,
                    display_output="abstract",
                    anchor_instrument=anchor,
                )
            )
        finally:
            await http2.aclose()
        assert result2.pages_fetched == 1
