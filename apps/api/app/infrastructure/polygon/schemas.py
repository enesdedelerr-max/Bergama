"""Provider-specific Polygon REST aggregate schemas (aliases only)."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

_PYTHON_FLOAT_REJECTED = "python float is not admitted for polygon financial fields"
_PYTHON_BOOL_REJECTED = "python bool is not admitted for polygon financial fields"


def _reject_python_float(value: object) -> object:
    if type(value) is float:
        raise ValueError(_PYTHON_FLOAT_REJECTED)
    if type(value) is bool:
        raise ValueError(_PYTHON_BOOL_REJECTED)
    return value


type PolygonFinancialNumber = Annotated[
    Decimal | int | str,
    BeforeValidator(_reject_python_float),
]


class PolygonAggBar(BaseModel):
    """Single aggregate bar from Polygon stocks custom bars."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    open: PolygonFinancialNumber = Field(alias="o")
    high: PolygonFinancialNumber = Field(alias="h")
    low: PolygonFinancialNumber = Field(alias="l")
    close: PolygonFinancialNumber = Field(alias="c")
    volume: PolygonFinancialNumber = Field(alias="v")
    vwap: PolygonFinancialNumber | None = Field(default=None, alias="vw")
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
