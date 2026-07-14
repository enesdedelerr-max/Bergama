"""Provider-specific Finnhub REST schemas (Issue #304A)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FinnhubCompanyProfile2(BaseModel):
    """Response for GET /stock/profile2."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    country: str | None = None
    currency: str | None = None
    exchange: str | None = None
    name: str | None = None
    ticker: str | None = None
    ipo: str | None = None
    market_capitalization: float | int | str | None = Field(
        default=None, alias="marketCapitalization"
    )
    share_outstanding: float | int | str | None = Field(default=None, alias="shareOutstanding")
    logo: str | None = None
    phone: str | None = None
    weburl: str | None = None
    finnhub_industry: str | None = Field(default=None, alias="finnhubIndustry")

    def is_empty(self) -> bool:
        return not any(
            [
                self.country,
                self.currency,
                self.exchange,
                self.name,
                self.ticker,
                self.ipo,
                self.market_capitalization is not None,
                self.share_outstanding is not None,
                self.logo,
                self.phone,
                self.weburl,
                self.finnhub_industry,
            ]
        )


class FinnhubBasicFinancials(BaseModel):
    """Response for GET /stock/metric?metric=all (flat metric map only)."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    symbol: str | None = None
    metric_type: str | None = Field(default=None, alias="metricType")
    metric: dict[str, Any] = Field(default_factory=dict)
    # series intentionally ignored for #304A mapping.
