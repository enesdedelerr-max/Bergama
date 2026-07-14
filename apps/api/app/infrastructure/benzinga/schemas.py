"""Typed Benzinga Newsfeed request/response schemas (Issue #304D)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BenzingaChannelTag(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    name: str | None = None


class BenzingaStock(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    name: str | None = None
    cusip: str | None = None
    isin: str | None = None
    exchange: str | None = None


class BenzingaImage(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    size: str | None = None
    url: str | None = None
    alt: str | None = None


class BenzingaNewsItem(BaseModel):
    """Official api.NewsItem fields used by the connector."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    id: int
    author: str | None = None
    created: str
    updated: str
    title: str
    teaser: str | None = None
    body: str | None = Field(
        default=None,
        description="Never mapped into NewsEvent; ignored even if present",
    )
    url: str | None = None
    image: tuple[BenzingaImage, ...] = ()
    channels: tuple[BenzingaChannelTag, ...] = ()
    stocks: tuple[BenzingaStock, ...] = ()
    tags: tuple[BenzingaChannelTag, ...] = ()
    importance_rank: int | None = None
    original_id: int | None = None

    @field_validator("channels", "stocks", "tags", "image", mode="before")
    @classmethod
    def empty_list_to_tuple(cls, value: object) -> object:
        if value is None:
            return ()
        return value
