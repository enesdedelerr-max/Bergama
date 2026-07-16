"""Immutable BrokerCapabilities with capability fingerprint (#405)."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.broker.hashing import build_capability_fingerprint
from app.orders.models import OrderType, TimeInForce


class BrokerCapabilities(BaseModel):
    """Immutable broker capability declaration. Validated before submit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    supported_order_types: tuple[OrderType, ...] = (
        OrderType.MARKET,
        OrderType.LIMIT,
    )
    supported_time_in_force: tuple[TimeInForce, ...] = (
        TimeInForce.DAY,
        TimeInForce.GTC,
    )
    supports_cancel: bool = True
    supports_replace: bool = False
    supports_fractional_quantity: bool = False
    supports_shorting: bool = False
    supports_client_order_id: bool = True
    supports_query: bool = False
    supports_reconciliation: bool = True
    supports_fill_ids: bool = True
    supports_event_sequence: bool = True
    capability_fingerprint: str | None = Field(default=None, min_length=64, max_length=64)

    def canonical_dict(self) -> dict[str, object]:
        return {
            "supported_order_types": [t.value for t in self.supported_order_types],
            "supported_time_in_force": [t.value for t in self.supported_time_in_force],
            "supports_cancel": self.supports_cancel,
            "supports_client_order_id": self.supports_client_order_id,
            "supports_event_sequence": self.supports_event_sequence,
            "supports_fill_ids": self.supports_fill_ids,
            "supports_fractional_quantity": self.supports_fractional_quantity,
            "supports_query": self.supports_query,
            "supports_reconciliation": self.supports_reconciliation,
            "supports_replace": self.supports_replace,
            "supports_shorting": self.supports_shorting,
        }

    @model_validator(mode="after")
    def attach_fingerprint(self) -> Self:
        fingerprint = build_capability_fingerprint(self.canonical_dict())
        if self.capability_fingerprint is None:
            object.__setattr__(self, "capability_fingerprint", fingerprint)
        elif self.capability_fingerprint != fingerprint:
            msg = "capability_fingerprint does not match canonical capabilities"
            raise ValueError(msg)
        return self

    def supports_order_type(self, order_type: OrderType) -> bool:
        return order_type in self.supported_order_types

    def supports_tif(self, tif: TimeInForce) -> bool:
        return tif in self.supported_time_in_force


def paper_broker_capabilities() -> BrokerCapabilities:
    return BrokerCapabilities()
