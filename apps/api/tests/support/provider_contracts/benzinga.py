"""Synthetic Benzinga fixtures mapped to canonical events (no copyrighted bodies)."""

from __future__ import annotations

from datetime import datetime

from app.infrastructure.benzinga.mapper import map_news_item
from app.infrastructure.benzinga.schemas import BenzingaNewsItem
from app.market_data.events.news import NewsEvent
from app.market_data.identity import InstrumentId
from tests.support.provider_contracts.clocks import OBSERVED_AT
from tests.support.provider_contracts.identities import equity_instrument, news_anchor_instrument

STORY_ID = 36444586
CREATED = "Mon, 01 Jan 2024 13:35:14 -0400"
UPDATED = "Mon, 01 Jan 2024 13:35:15 -0400"
UPDATED_LATER = "Mon, 01 Jan 2024 14:00:00 -0400"


def news_item_payload(
    *,
    story_id: int = STORY_ID,
    updated: str = UPDATED,
    stocks: list[dict[str, str]] | None = None,
    body: str | None = "SYNTHETIC_BODY_MUST_NEVER_MAP",
) -> dict[str, object]:
    return {
        "id": story_id,
        "author": "Synthetic Desk",
        "created": CREATED,
        "updated": updated,
        "title": "Synthetic contract fixture headline",
        "teaser": "Synthetic teaser only.",
        "body": body,
        "url": "https://www.benzinga.com/news/test/synthetic-fixture",
        "channels": [{"name": "Markets"}],
        "tags": [{"name": "Synthetic"}],
        "stocks": stocks if stocks is not None else [{"name": "AAPL"}],
        "importance_rank": 1,
        "original_id": 1001,
    }


def news_events(
    *,
    ticker_to_instrument: dict[str, InstrumentId] | None = None,
    anchor_instrument: InstrumentId | None = None,
    observed_at: datetime | None = None,
    updated: str = UPDATED,
    stocks: list[dict[str, str]] | None = None,
) -> tuple[NewsEvent, ...]:
    item = BenzingaNewsItem.model_validate(news_item_payload(updated=updated, stocks=stocks))
    mapping = ticker_to_instrument
    if mapping is None and stocks != []:
        mapping = {"AAPL": equity_instrument()}
    if mapping is None:
        mapping = {}
    return map_news_item(
        item,
        ticker_to_instrument=mapping,
        anchor_instrument=anchor_instrument,
        observed_at=observed_at or OBSERVED_AT,
        endpoint_ref="https://api.benzinga.com/api/v2/news?page=0&displayOutput=abstract",
    )


def zero_ticker_news(*, anchor: InstrumentId | None = None) -> tuple[NewsEvent, ...]:
    return news_events(
        stocks=[],
        ticker_to_instrument={},
        anchor_instrument=anchor or news_anchor_instrument(),
    )
