"""Broker adapter lifecycle states (#405)."""

from __future__ import annotations

from enum import StrEnum


class BrokerAdapterLifecycle(StrEnum):
    CREATED = "CREATED"
    STARTING = "STARTING"
    READY = "READY"
    STOPPING = "STOPPING"
    CLOSED = "CLOSED"
