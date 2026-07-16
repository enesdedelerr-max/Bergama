"""Order Management System downstream ports — protocol only (#404/#405)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol

from app.orders.events import BrokerOrderCommand, FillEvent
from app.orders.models import OrderSnapshot

if TYPE_CHECKING:
    from app.broker.capabilities import BrokerCapabilities
    from app.broker.models import BrokerCancelResult, BrokerSubmissionResult
    from app.broker.outcomes import BrokerCommandOutcome


class BrokerOrderPort(Protocol):
    """Infrastructure-neutral broker command port. Never returns None (#405)."""

    def capabilities(self) -> BrokerCapabilities: ...

    async def submit(self, command: BrokerOrderCommand) -> BrokerSubmissionResult: ...

    async def cancel(self, command: BrokerOrderCommand) -> BrokerCancelResult: ...


class FillEventPort(Protocol):
    """Downstream fill facts only — must not call PortfolioService in #404/#405."""

    async def publish_fill(self, fill: FillEvent) -> None: ...


class InMemoryBrokerOrderPort:
    """Typed in-memory OMS broker port. Records commands; returns ACKNOWLEDGED."""

    def __init__(
        self,
        *,
        broker_name: str = "in-memory",
        broker_account_id: str = "in-memory-account",
        capabilities: BrokerCapabilities | None = None,
    ) -> None:
        from app.broker.capabilities import paper_broker_capabilities

        self._commands: list[BrokerOrderCommand] = []
        self.fail_next: Exception | None = None
        self.force_outcome: BrokerCommandOutcome | None = None
        self._broker_name = broker_name
        self._broker_account_id = broker_account_id
        self._capabilities = capabilities or paper_broker_capabilities()

    def capabilities(self) -> BrokerCapabilities:
        return self._capabilities

    async def submit(self, command: BrokerOrderCommand) -> BrokerSubmissionResult:
        from app.broker.hashing import build_submission_identity, executable_order_hash
        from app.broker.models import BrokerSubmissionResult
        from app.broker.outcomes import BrokerCommandOutcome

        if self.fail_next is not None:
            exc = self.fail_next
            self.fail_next = None
            raise exc
        self._commands.append(command)
        assert command.executable_order is not None
        order_hash = executable_order_hash(command.executable_order)
        submission_id = build_submission_identity(
            broker_name=self._broker_name,
            broker_account_id=self._broker_account_id,
            client_order_id=command.executable_order.client_order_id.value,
            executable_order_hash_value=order_hash,
        )
        outcome = self.force_outcome or BrokerCommandOutcome.ACKNOWLEDGED
        self.force_outcome = None
        return BrokerSubmissionResult(
            outcome=outcome,
            submission_identity=submission_id,
            broker_order_id=f"mem-{command.order_id.value[:16]}",
            correlation_id=command.correlation_id,
            causation_id=command.causation_id,
        )

    async def cancel(self, command: BrokerOrderCommand) -> BrokerCancelResult:
        from app.broker.models import BrokerCancelResult
        from app.broker.outcomes import BrokerCommandOutcome

        if self.fail_next is not None:
            exc = self.fail_next
            self.fail_next = None
            raise exc
        self._commands.append(command)
        outcome = self.force_outcome or BrokerCommandOutcome.ACKNOWLEDGED
        self.force_outcome = None
        return BrokerCancelResult(
            outcome=outcome,
            broker_order_id=command.broker_order_id,
            correlation_id=command.correlation_id,
            causation_id=command.causation_id,
        )

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
    """Optional placeholder for future broker-order query."""

    async def get_broker_order(self, order: OrderSnapshot) -> None:
        return None
