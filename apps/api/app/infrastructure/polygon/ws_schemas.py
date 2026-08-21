"""Typed Polygon stocks WebSocket message schemas (Issue #303)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.infrastructure.polygon.schemas import PolygonFinancialNumber


class PolygonWsStatusMessage(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    ev: Literal["status"] = "status"
    status: str
    message: str | None = None


class PolygonWsTradeMessage(BaseModel):
    """Stocks trade tick (`ev=T`)."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    ev: Literal["T"] = "T"
    sym: str
    x: int | str | None = None
    i: int | str | None = None
    z: int | str | None = None
    p: PolygonFinancialNumber
    s: PolygonFinancialNumber
    c: list[int] | None = None
    t: int

    @field_validator("sym")
    @classmethod
    def strip_sym(cls, value: str) -> str:
        text = value.strip().upper()
        if not text:
            msg = "sym must be non-empty"
            raise ValueError(msg)
        return text


class PolygonWsQuoteMessage(BaseModel):
    """Stocks NBBO quote tick (`ev=Q`)."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    ev: Literal["Q"] = "Q"
    sym: str
    bx: int | str | None = None
    bp: PolygonFinancialNumber
    bs: PolygonFinancialNumber
    ax: int | str | None = None
    ap: PolygonFinancialNumber
    as_: PolygonFinancialNumber = Field(alias="as")
    c: int | None = None
    t: int
    z: int | str | None = None

    @field_validator("sym")
    @classmethod
    def strip_sym(cls, value: str) -> str:
        text = value.strip().upper()
        if not text:
            msg = "sym must be non-empty"
            raise ValueError(msg)
        return text


class PolygonWsMinuteAggregateMessage(BaseModel):
    """Stocks per-minute aggregate (`ev=AM`)."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    ev: Literal["AM"] = "AM"
    sym: str
    v: PolygonFinancialNumber
    av: PolygonFinancialNumber | None = None
    op: PolygonFinancialNumber | None = None
    vw: PolygonFinancialNumber | None = None
    o: PolygonFinancialNumber
    c: PolygonFinancialNumber
    h: PolygonFinancialNumber
    low: PolygonFinancialNumber = Field(alias="l")
    a: PolygonFinancialNumber | None = None
    z: PolygonFinancialNumber | None = None
    s: int
    e: int

    @field_validator("sym")
    @classmethod
    def strip_sym(cls, value: str) -> str:
        text = value.strip().upper()
        if not text:
            msg = "sym must be non-empty"
            raise ValueError(msg)
        return text


PolygonWsDataMessage = (
    PolygonWsTradeMessage | PolygonWsQuoteMessage | PolygonWsMinuteAggregateMessage
)


def parse_ws_message(
    payload: dict[str, Any],
) -> (
    PolygonWsStatusMessage
    | PolygonWsTradeMessage
    | PolygonWsQuoteMessage
    | PolygonWsMinuteAggregateMessage
):
    """Parse one Polygon WS object; reject unsupported data event types."""
    from app.infrastructure.polygon.errors import PolygonWebsocketProtocolError

    ev = payload.get("ev")
    if ev == "status":
        return PolygonWsStatusMessage.model_validate(payload)
    if ev == "T":
        return PolygonWsTradeMessage.model_validate(payload)
    if ev == "Q":
        return PolygonWsQuoteMessage.model_validate(payload)
    if ev == "AM":
        return PolygonWsMinuteAggregateMessage.model_validate(payload)
    if ev == "A":
        raise PolygonWebsocketProtocolError("second aggregates (ev=A) are not supported in #303")
    raise PolygonWebsocketProtocolError(f"unsupported polygon websocket event type {ev!r}")
