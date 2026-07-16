"""Order Management System downstream ports — protocol only (#404)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.orders.events import BrokerOrderCommand, FillEvent
from app.orders.models import OrderSnapshot


class BrokerSubmitAck(Protocol):
    """Typed acknowledgement — never a provider SDK object."""

    @property
    def accepted(self) -> bool: ...


class BrokerOrderPort(Protocol):
    """Infrastructure-neutral broker command port. No SDK/DTO leakage."""

    async def submit(self, command: BrokerOrderCommand) -> None: ...

    async def cancel(self, command: BrokerOrderCommand) -> None: ...


class FillEventPort(Protocol):
    """Downstream fill facts only — must not call PortfolioService in #404."""

    async def publish_fill(self, fill: FillEvent) -> None: ...


class InMemoryBrokerOrderPort:
    def __init__(self) -> None:
        self._commands: list[BrokerOrderCommand] = []
        self.fail_next: Exception | None = None

    async def submit(self, command: BrokerOrderCommand) -> None:
        if self.fail_next is not None:
            exc = self.fail_next
            self.fail_next = None
            raise exc
        self._commands.append(command)

    async def cancel(self, command: BrokerOrderCommand) -> None:
        if self.fail_next is not None:
            exc = self.fail_next
            self.fail_next = None
            raise exc
        self._commands.append(command)

    @property
    def commands(self) -> Sequence[BrokerOrderCommand]:
        return tuple(self._commands)

    def clear(self) -> None:
        self._commands.clear()


class InMemoryFillEventPort:
    def __init__(self) -> None:
        self._fills: list[FillEvent] = []
        self.fail_next: Exception | None = None

    async def publish_fill(self, fill: FillEvent) -> None:
        if self.fail_next is not None:
            exc = self.fail_next
            self.fail_next = None
            raise exc
        self._fills.append(fill)

    @property
    def fills(self) -> Sequence[FillEvent]:
        return tuple(self._fills)

    def clear(self) -> None:
        self._fills.clear()


class InMemoryOrderQueryPort:
    """Optional placeholder for future broker-order query (#405+)."""

    async def get_broker_order(self, order: OrderSnapshot) -> None:
        return None
