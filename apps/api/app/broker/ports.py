"""BrokerOrderPort protocol — typed results only, never None (#405)."""

from __future__ import annotations

from typing import Protocol

from app.broker.capabilities import BrokerCapabilities
from app.broker.models import (
    BrokerCancelResult,
    BrokerSubmissionResult,
    CancelExecutableOrder,
    SubmitExecutableOrder,
)
from app.orders.events import BrokerOrderCommand
from app.orders.models import ExecutableOrder


class BrokerOrderPort(Protocol):
    """Infrastructure-neutral broker command port.

    Never returns None. Never exposes SDK objects, provider DTOs, or raw
    provider exceptions. Never accesses OMS repositories.
    """

    def capabilities(self) -> BrokerCapabilities: ...

    async def submit(self, command: SubmitExecutableOrder) -> BrokerSubmissionResult: ...

    async def cancel(self, command: CancelExecutableOrder) -> BrokerCancelResult: ...


class BrokerOrderCommandPort(Protocol):
    """OMS-facing adapter over BrokerOrderCommand → typed broker results."""

    def capabilities(self) -> BrokerCapabilities: ...

    async def submit(self, command: BrokerOrderCommand) -> BrokerSubmissionResult: ...

    async def cancel(self, command: BrokerOrderCommand) -> BrokerCancelResult: ...


def executable_from_oms_command(command: BrokerOrderCommand) -> ExecutableOrder:
    if command.executable_order is None:
        msg = "SUBMIT requires executable_order"
        raise ValueError(msg)
    return command.executable_order
