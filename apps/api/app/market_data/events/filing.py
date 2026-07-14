"""Canonical regulatory filing event."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from app.market_data.enums import MarketEventType
from app.market_data.events.base import MarketEventBase


class FilingEvent(MarketEventBase):
    """SEC EDGAR-style filing metadata after normalization."""

    event_type: Literal[MarketEventType.FILING] = MarketEventType.FILING
    form_type: str = Field(min_length=1, max_length=32)
    accession_number: str = Field(min_length=1, max_length=64)
    title: str | None = Field(default=None, max_length=512)
    document_ref: str | None = Field(
        default=None,
        max_length=512,
        description="Opaque document reference — not raw filing body",
    )

    @field_validator("form_type", "accession_number", "title", "document_ref")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if not text:
            msg = "value must be non-empty"
            raise ValueError(msg)
        return text
