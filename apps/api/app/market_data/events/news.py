"""Canonical news / headline event."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from app.market_data.enums import MarketEventType
from app.market_data.events.base import MarketEventBase


class NewsEvent(MarketEventBase):
    """Normalized news / headline observation."""

    event_type: Literal[MarketEventType.NEWS] = MarketEventType.NEWS
    headline: str = Field(min_length=1, max_length=1024)
    summary: str | None = Field(default=None, max_length=4096)
    url_ref: str | None = Field(default=None, max_length=1024)
    language: str | None = Field(default=None, min_length=2, max_length=8)
    topics: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("headline", "summary", "url_ref", "language")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if not text:
            msg = "value must be non-empty"
            raise ValueError(msg)
        return text

    @field_validator("topics")
    @classmethod
    def validate_topics(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) > 32:
            msg = "topics may contain at most 32 entries"
            raise ValueError(msg)
        cleaned: list[str] = []
        for item in value:
            text = item.strip()
            if not text or len(text) > 64:
                msg = "invalid topic entry"
                raise ValueError(msg)
            cleaned.append(text)
        return tuple(cleaned)
