"""Provider-specific Polygon REST aggregate schemas (aliases only)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PolygonAggBar(BaseModel):
    """Single aggregate bar from Polygon stocks custom bars."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    open: float | int | str = Field(alias="o")
    high: float | int | str = Field(alias="h")
    low: float | int | str = Field(alias="l")
    close: float | int | str = Field(alias="c")
    volume: float | int | str = Field(alias="v")
    vwap: float | int | str | None = Field(default=None, alias="vw")
    timestamp_ms: int = Field(alias="t")
    transactions: int | None = Field(default=None, alias="n")
    otc: bool | None = None


class PolygonAggsResponse(BaseModel):
    """Polygon `/v2/aggs/...` response envelope."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    status: str | None = None
    request_id: str | None = None
    ticker: str | None = None
    adjusted: bool | None = None
    query_count: int | None = Field(default=None, alias="queryCount")
    results_count: int | None = Field(default=None, alias="resultsCount")
    count: int | None = None
    next_url: str | None = None
    results: list[PolygonAggBar] = Field(default_factory=list)
